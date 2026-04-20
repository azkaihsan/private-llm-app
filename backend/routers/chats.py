from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid
import os
import base64

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import litellm

from config import db, logger
from auth import get_current_user
from storage import get_object, extract_text_from_file, web_search
from models import (
    ChatCreate, ChatUpdate, MessageCreate, ChatImport,
    ALL_MODELS, EMERGENT_PROVIDERS, PROVIDER_BASE_URLS, MODEL_PROVIDER_MAP,
)

router = APIRouter()


@router.get("/chats")
async def get_chats(user=Depends(get_current_user)):
    chats = await db.chats.find({"user_id": user["id"], "archived": {"$ne": True}}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return chats


@router.post("/chats")
async def create_chat(data: ChatCreate, user=Depends(get_current_user)):
    chat = {
        "id": str(uuid.uuid4()),
        "title": data.title or "New Chat",
        "model": data.model,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.chats.insert_one({**chat, "_id": chat["id"]})
    return chat


@router.get("/chats/archived")
async def get_archived_chats(user=Depends(get_current_user)):
    chats = await db.chats.find({"user_id": user["id"], "archived": True}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return chats


@router.get("/chats/{chat_id}")
async def get_chat(chat_id: str, user=Depends(get_current_user)):
    chat = await db.chats.find_one({"id": chat_id, "user_id": user["id"]}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    chat["messages"] = messages
    return chat


@router.put("/chats/{chat_id}")
async def update_chat(chat_id: str, data: ChatUpdate, user=Depends(get_current_user)):
    result = await db.chats.update_one({"id": chat_id, "user_id": user["id"]}, {"$set": {"title": data.title}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}


@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, user=Depends(get_current_user)):
    await db.chats.delete_one({"id": chat_id, "user_id": user["id"]})
    await db.messages.delete_many({"chat_id": chat_id})
    return {"status": "ok"}


@router.post("/chats/{chat_id}/messages")
async def send_message(chat_id: str, data: MessageCreate, user=Depends(get_current_user)):
    chat = await db.chats.find_one({"id": chat_id, "user_id": user["id"]}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    now_ts = datetime.now(timezone.utc).isoformat()

    # Process file attachments
    attachments = []
    file_text_parts = []
    image_b64_list = []

    if data.file_ids:
        for fid in data.file_ids:
            file_rec = await db.files.find_one({"id": fid, "user_id": user["id"], "is_deleted": False}, {"_id": 0})
            if not file_rec:
                continue
            attachments.append({
                "id": file_rec["id"],
                "filename": file_rec["original_filename"],
                "content_type": file_rec["content_type"],
                "size": file_rec["size"],
                "is_image": file_rec.get("is_image", False),
            })
            try:
                file_data, _ = get_object(file_rec["storage_path"])
                if file_rec.get("is_image", False):
                    b64 = base64.b64encode(file_data).decode("utf-8")
                    mime = file_rec["content_type"] or "image/png"
                    image_b64_list.append({"b64": b64, "mime": mime})
                else:
                    text = extract_text_from_file(file_data, file_rec["original_filename"], file_rec["content_type"])
                    if text:
                        file_text_parts.append(f"[File: {file_rec['original_filename']}]\n{text}")
            except Exception as e:
                logger.error(f"Error processing file {fid}: {e}")

    # Save user message with attachments
    user_msg = {
        "id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "role": "user",
        "content": data.content,
        "attachments": attachments if attachments else None,
        "timestamp": now_ts,
    }
    await db.messages.insert_one({**user_msg, "_id": user_msg["id"]})

    # Auto-title on first message
    existing = await db.messages.count_documents({"chat_id": chat_id})
    if existing <= 1:
        title = data.content[:50] + ("..." if len(data.content) > 50 else "")
        if not data.content.strip() and attachments:
            title = f"[{attachments[0]['filename']}]"
        await db.chats.update_one({"id": chat_id}, {"$set": {"title": title}})

    # Get LLM response
    model_id = chat.get("model", "gpt-4o")
    provider = MODEL_PROVIDER_MAP.get(model_id, "openai")

    if provider == "openai_compatible" or (model_id.startswith("openai/") and provider not in EMERGENT_PROVIDERS):
        provider = "openai_compatible"

    conn = await db.connections.find_one({"_id": "global"}, {"_id": 0})
    default_key = os.environ.get("EMERGENT_LLM_KEY", "")

    if conn:
        prov_config = conn.get("providers", {}).get(provider, {})
        if prov_config.get("useEmergentKey", True) and provider in EMERGENT_PROVIDERS:
            api_key = default_key
        else:
            api_key = prov_config.get("apiKey", "")
        model_params = conn.get("modelParams", {})
    else:
        api_key = default_key
        model_params = {}

    temperature = data.temperature if data.temperature is not None else model_params.get("temperature", 0.7)
    max_tokens = data.max_tokens if data.max_tokens is not None else model_params.get("maxTokens", 4096)
    top_p = data.top_p if data.top_p is not None else model_params.get("topP", 1.0)

    # Build user prompt with file context
    user_prompt = data.content or ""
    if file_text_parts:
        user_prompt = user_prompt + "\n\n" + "\n\n".join(file_text_parts) if user_prompt else "\n\n".join(file_text_parts)

    # Web search
    search_context = ""
    if user_prompt.strip():
        search_context = web_search(user_prompt[:200], max_results=5)

    try:
        app_settings = await db.app_settings.find_one({"_id": "global"}, {"_id": 0})
        base_system_prompt = (app_settings or {}).get("systemPrompt", "You are a helpful AI assistant. You provide clear, accurate, and well-formatted responses using markdown when appropriate.")

        if search_context:
            system_prompt = base_system_prompt + "\n\nYou have access to recent web search results. Use them to provide up-to-date, accurate information. Cite sources when relevant using [Source](url) format.\n\n--- Web Search Results ---\n" + search_context + "\n--- End of Search Results ---"
        else:
            system_prompt = base_system_prompt

        # Build chat history
        history_msgs = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).to_list(50)

        if provider in EMERGENT_PROVIDERS:
            llm = LlmChat(
                api_key=api_key,
                session_id=chat_id,
                system_message=system_prompt
            ).with_model(provider, model_id)

            if image_b64_list:
                file_contents = [ImageContent(image_base64=img["b64"]) for img in image_b64_list]
                user_message = UserMessage(text=user_prompt or "What do you see in this image?", file_contents=file_contents)
            else:
                user_message = UserMessage(text=user_prompt)
            response_text = await llm.send_message(user_message)
        else:
            messages_for_llm = [{"role": "system", "content": system_prompt}]
            for hm in history_msgs:
                messages_for_llm.append({"role": hm["role"], "content": hm["content"]})

            if image_b64_list:
                content_parts = []
                if user_prompt:
                    content_parts.append({"type": "text", "text": user_prompt})
                for img in image_b64_list:
                    content_parts.append({"type": "image_url", "image_url": {"url": f"data:{img['mime']};base64,{img['b64']}"}})
                messages_for_llm.append({"role": "user", "content": content_parts})
            else:
                messages_for_llm.append({"role": "user", "content": user_prompt})

            litellm_model = model_id
            extra_kwargs = {}

            if provider == "deepseek":
                os.environ["DEEPSEEK_API_KEY"] = api_key
            elif provider == "qwen":
                base_url = (conn or {}).get("providers", {}).get("qwen", {}).get("baseUrl", PROVIDER_BASE_URLS.get("qwen", ""))
                extra_kwargs["api_base"] = base_url
                extra_kwargs["api_key"] = api_key
            elif provider == "grok":
                os.environ["XAI_API_KEY"] = api_key
            elif provider == "perplexity":
                os.environ["PERPLEXITYAI_API_KEY"] = api_key
            elif provider == "bedrock":
                bedrock_config = (conn or {}).get("providers", {}).get("bedrock", {})
                os.environ["AWS_ACCESS_KEY_ID"] = bedrock_config.get("awsAccessKey", "")
                os.environ["AWS_SECRET_ACCESS_KEY"] = bedrock_config.get("awsSecretKey", "")
                os.environ["AWS_REGION_NAME"] = bedrock_config.get("awsRegion", "us-east-1")
            elif provider == "openai_compatible":
                compat_config = (conn or {}).get("providers", {}).get("openai_compatible", {})
                base_url = compat_config.get("baseUrl", "")
                extra_kwargs["api_base"] = base_url
                extra_kwargs["api_key"] = api_key

            response = await litellm.acompletion(
                model=litellm_model,
                messages=messages_for_llm,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **extra_kwargs,
            )
            response_text = response.choices[0].message.content

    except Exception as e:
        logger.error(f"LLM error for provider={provider} model={model_id}: {e}")
        response_text = f"Sorry, I encountered an error while generating a response. Please try again.\n\nError: {str(e)}"

    ai_msg = {
        "id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "role": "assistant",
        "content": response_text,
        "web_searched": bool(search_context),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.messages.insert_one({**ai_msg, "_id": ai_msg["id"]})

    return {
        "user_message": {k: v for k, v in user_msg.items() if k != "_id"},
        "assistant_message": {k: v for k, v in ai_msg.items() if k != "_id"},
    }


# ===== Archive, Export, Import =====

@router.put("/chats/{chat_id}/archive")
async def archive_chat(chat_id: str, user=Depends(get_current_user)):
    result = await db.chats.update_one({"id": chat_id, "user_id": user["id"]}, {"$set": {"archived": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}


@router.put("/chats/{chat_id}/unarchive")
async def unarchive_chat(chat_id: str, user=Depends(get_current_user)):
    result = await db.chats.update_one({"id": chat_id, "user_id": user["id"]}, {"$set": {"archived": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}


@router.get("/chats/{chat_id}/export")
async def export_chat(chat_id: str, user=Depends(get_current_user)):
    chat = await db.chats.find_one({"id": chat_id, "user_id": user["id"]}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    return {
        "version": "1.0",
        "source": "open-webui-clone",
        "chat": chat,
        "messages": messages,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/chats/import")
async def import_chat(data: ChatImport, user=Depends(get_current_user)):
    new_chat_id = str(uuid.uuid4())
    chat_data = {
        "id": new_chat_id,
        "title": data.chat.get("title", "Imported Chat"),
        "model": data.chat.get("model", "gpt-4o"),
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "archived": False,
    }
    await db.chats.insert_one({**chat_data, "_id": new_chat_id})

    for msg in data.messages:
        new_msg = {
            "id": str(uuid.uuid4()),
            "chat_id": new_chat_id,
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
            "timestamp": msg.get("timestamp", datetime.now(timezone.utc).isoformat()),
        }
        await db.messages.insert_one({**new_msg, "_id": new_msg["id"]})

    return {"status": "ok", "chat_id": new_chat_id, "chat": chat_data}


@router.delete("/chats/archived/all")
async def delete_all_archived(user=Depends(get_current_user)):
    archived = await db.chats.find({"user_id": user["id"], "archived": True}, {"id": 1, "_id": 0}).to_list(1000)
    for chat in archived:
        await db.messages.delete_many({"chat_id": chat["id"]})
    await db.chats.delete_many({"user_id": user["id"], "archived": True})
    return {"status": "ok", "deleted_count": len(archived)}
