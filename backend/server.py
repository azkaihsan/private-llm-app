from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
import litellm


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the router in the main app - moved to after all routes are defined

# ===== Chat Models =====
ALL_MODELS = {
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
        {"id": "gpt-4.1-mini", "name": "GPT-4.1 mini", "provider": "openai"},
        {"id": "gpt-5.1", "name": "GPT-5.1", "provider": "openai"},
        {"id": "gpt-5-mini", "name": "GPT-5 mini", "provider": "openai"},
    ],
    "anthropic": [
        {"id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5", "provider": "anthropic"},
        {"id": "claude-4-sonnet-20250514", "name": "Claude 4 Sonnet", "provider": "anthropic"},
    ],
    "gemini": [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "gemini"},
    ],
    "deepseek": [
        {"id": "deepseek/deepseek-chat", "name": "DeepSeek V3", "provider": "deepseek"},
        {"id": "deepseek/deepseek-reasoner", "name": "DeepSeek R1", "provider": "deepseek"},
    ],
    "qwen": [
        {"id": "openai/qwen-max", "name": "Qwen Max", "provider": "qwen"},
        {"id": "openai/qwen-plus", "name": "Qwen Plus", "provider": "qwen"},
        {"id": "openai/qwen-turbo", "name": "Qwen Turbo", "provider": "qwen"},
    ],
    "grok": [
        {"id": "xai/grok-3", "name": "Grok 3", "provider": "grok"},
        {"id": "xai/grok-3-mini", "name": "Grok 3 Mini", "provider": "grok"},
    ],
    "perplexity": [
        {"id": "perplexity/sonar-pro", "name": "Sonar Pro", "provider": "perplexity"},
        {"id": "perplexity/sonar", "name": "Sonar", "provider": "perplexity"},
        {"id": "perplexity/sonar-reasoning-pro", "name": "Sonar Reasoning Pro", "provider": "perplexity"},
    ],
    "bedrock": [
        {"id": "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0", "name": "Claude 3.5 Sonnet (Bedrock)", "provider": "bedrock"},
        {"id": "bedrock/amazon.nova-pro-v1:0", "name": "Amazon Nova Pro", "provider": "bedrock"},
        {"id": "bedrock/amazon.nova-lite-v1:0", "name": "Amazon Nova Lite", "provider": "bedrock"},
    ],
    "openai_compatible": [],
}

# Providers that use Emergent key (only openai, anthropic, gemini)
EMERGENT_PROVIDERS = {"openai", "anthropic", "gemini"}

# Provider base URLs for non-Emergent providers
PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "grok": "https://api.x.ai/v1",
    "perplexity": "https://api.perplexity.ai",
}

FLAT_MODELS = [m for models in ALL_MODELS.values() for m in models]
MODEL_PROVIDER_MAP = {m["id"]: m["provider"] for m in FLAT_MODELS}

class ChatCreate(BaseModel):
    title: str = ""
    model: str = "gpt-4o"

class ChatUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

# ===== Connection & Model Endpoints =====

@api_router.get("/connections")
async def get_connections():
    doc = await db.connections.find_one({"_id": "global"}, {"_id": 0})
    if not doc:
        default_key = os.environ.get("EMERGENT_LLM_KEY", "")
        return {
            "providers": {
                "openai": {"enabled": True, "apiKey": default_key, "name": "OpenAI", "useEmergentKey": True},
                "anthropic": {"enabled": True, "apiKey": default_key, "name": "Anthropic", "useEmergentKey": True},
                "gemini": {"enabled": True, "apiKey": default_key, "name": "Google Gemini", "useEmergentKey": True},
                "deepseek": {"enabled": False, "apiKey": "", "name": "DeepSeek", "useEmergentKey": False, "baseUrl": "https://api.deepseek.com/v1"},
                "qwen": {"enabled": False, "apiKey": "", "name": "Qwen", "useEmergentKey": False, "baseUrl": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"},
                "grok": {"enabled": False, "apiKey": "", "name": "Grok (xAI)", "useEmergentKey": False, "baseUrl": "https://api.x.ai/v1"},
                "perplexity": {"enabled": False, "apiKey": "", "name": "Perplexity", "useEmergentKey": False, "baseUrl": "https://api.perplexity.ai"},
                "bedrock": {"enabled": False, "apiKey": "", "name": "Amazon Bedrock", "useEmergentKey": False, "awsRegion": "us-east-1", "awsAccessKey": "", "awsSecretKey": ""},
                "openai_compatible": {"enabled": False, "apiKey": "", "name": "OpenAI Compatible", "useEmergentKey": False, "baseUrl": "", "customModels": ""},
            },
            "defaultModel": "gpt-4o",
            "modelParams": {"temperature": 0.7, "maxTokens": 4096, "topP": 1.0},
            "disabledModels": [],
        }
    return doc

@api_router.put("/connections")
async def update_connections(data: dict):
    await db.connections.update_one(
        {"_id": "global"},
        {"$set": data},
        upsert=True
    )
    return {"status": "ok"}

class TestConnectionRequest(BaseModel):
    provider: str
    apiKey: str

@api_router.post("/connections/test")
async def test_connection(data: TestConnectionRequest):
    try:
        llm = LlmChat(
            api_key=data.apiKey,
            session_id=f"test-{uuid.uuid4()}",
            system_message="Reply with exactly: CONNECTION_OK"
        ).with_model(data.provider, None)
        result = await llm.send_message(UserMessage(text="Say CONNECTION_OK"))
        return {"status": "ok", "message": "Connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@api_router.get("/models")
async def get_models():
    conn = await db.connections.find_one({"_id": "global"}, {"_id": 0})
    if not conn:
        # Use default configuration - only enabled providers (openai, anthropic, gemini)
        providers = {
            "openai": {"enabled": True},
            "anthropic": {"enabled": True},
            "gemini": {"enabled": True},
            "deepseek": {"enabled": False},
            "qwen": {"enabled": False},
            "grok": {"enabled": False},
            "perplexity": {"enabled": False},
            "bedrock": {"enabled": False},
            "openai_compatible": {"enabled": False},
        }
        disabled = set()
    else:
        providers = conn.get("providers", {})
        disabled = set(conn.get("disabledModels", []))
    
    result = []
    for provider_key, models in ALL_MODELS.items():
        if provider_key == "openai_compatible":
            continue
        prov_config = providers.get(provider_key, {})
        if prov_config.get("enabled", False if provider_key not in EMERGENT_PROVIDERS else True):
            for m in models:
                model_entry = {**m, "enabled": m["id"] not in disabled}
                result.append(model_entry)

    # Add custom OpenAI Compatible models
    compat_config = providers.get("openai_compatible", {})
    if compat_config.get("enabled", False) and compat_config.get("customModels", ""):
        custom_models = [m.strip() for m in compat_config["customModels"].split(",") if m.strip()]
        for cm in custom_models:
            model_entry = {"id": f"openai/{cm}", "name": cm, "provider": "openai_compatible", "enabled": f"openai/{cm}" not in disabled}
            result.append(model_entry)

    return result

# ===== Chat Endpoints =====

@api_router.get("/chats")
async def get_chats():
    chats = await db.chats.find({"archived": {"$ne": True}}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return chats

@api_router.post("/chats")
async def create_chat(data: ChatCreate):
    chat = {
        "id": str(uuid.uuid4()),
        "title": data.title or "New Chat",
        "model": data.model,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.chats.insert_one({**chat, "_id": chat["id"]})
    return chat

@api_router.get("/chats/archived")
async def get_archived_chats():
    chats = await db.chats.find({"archived": True}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return chats

@api_router.get("/chats/{chat_id}")
async def get_chat(chat_id: str):
    chat = await db.chats.find_one({"id": chat_id}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = await db.messages.find(
        {"chat_id": chat_id}, {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    chat["messages"] = messages
    return chat

@api_router.put("/chats/{chat_id}")
async def update_chat(chat_id: str, data: ChatUpdate):
    result = await db.chats.update_one({"id": chat_id}, {"$set": {"title": data.title}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}

@api_router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    await db.chats.delete_one({"id": chat_id})
    await db.messages.delete_many({"chat_id": chat_id})
    return {"status": "ok"}

@api_router.post("/chats/{chat_id}/messages")
async def send_message(chat_id: str, data: MessageCreate):
    chat = await db.chats.find_one({"id": chat_id}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    now_ts = datetime.now(timezone.utc).isoformat()

    # Save user message
    user_msg = {
        "id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "role": "user",
        "content": data.content,
        "timestamp": now_ts,
    }
    await db.messages.insert_one({**user_msg, "_id": user_msg["id"]})

    # Auto-title on first message
    existing = await db.messages.count_documents({"chat_id": chat_id})
    if existing <= 1:
        title = data.content[:50] + ("..." if len(data.content) > 50 else "")
        await db.chats.update_one({"id": chat_id}, {"$set": {"title": title}})

    # Get LLM response
    model_id = chat.get("model", "gpt-4o")
    provider = MODEL_PROVIDER_MAP.get(model_id, "openai")

    # For openai_compatible custom models, check if model_id starts with "openai/"
    if provider == "openai_compatible" or (model_id.startswith("openai/") and provider not in EMERGENT_PROVIDERS):
        provider = "openai_compatible"

    # Load connection config for the correct API key and params
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

    # Override with per-message params if provided
    temperature = data.temperature if data.temperature is not None else model_params.get("temperature", 0.7)
    max_tokens = data.max_tokens if data.max_tokens is not None else model_params.get("maxTokens", 4096)
    top_p = data.top_p if data.top_p is not None else model_params.get("topP", 1.0)

    try:
        # Load custom system prompt from settings
        app_settings = await db.app_settings.find_one({"_id": "global"}, {"_id": 0})
        system_prompt = (app_settings or {}).get("systemPrompt", "You are a helpful AI assistant. You provide clear, accurate, and well-formatted responses using markdown when appropriate.")

        # Build chat history for context
        history_msgs = await db.messages.find(
            {"chat_id": chat_id}, {"_id": 0}
        ).sort("timestamp", 1).to_list(50)
        messages_for_llm = [{"role": "system", "content": system_prompt}]
        for hm in history_msgs:
            messages_for_llm.append({"role": hm["role"], "content": hm["content"]})

        if provider in EMERGENT_PROVIDERS:
            # Use emergentintegrations for OpenAI, Anthropic, Gemini
            llm = LlmChat(
                api_key=api_key,
                session_id=chat_id,
                system_message=system_prompt
            ).with_model(provider, model_id)
            user_message = UserMessage(text=data.content)
            response_text = await llm.send_message(user_message)
        else:
            # Use litellm for DeepSeek, Qwen, Grok, Perplexity, Bedrock, OpenAI Compatible
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.messages.insert_one({**ai_msg, "_id": ai_msg["id"]})

    # Return both messages without _id
    return {
        "user_message": {k: v for k, v in user_msg.items() if k != "_id"},
        "assistant_message": {k: v for k, v in ai_msg.items() if k != "_id"},
    }

# ===== Archive, Export, Import Endpoints =====

@api_router.put("/chats/{chat_id}/archive")
async def archive_chat(chat_id: str):
    result = await db.chats.update_one({"id": chat_id}, {"$set": {"archived": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}

@api_router.put("/chats/{chat_id}/unarchive")
async def unarchive_chat(chat_id: str):
    result = await db.chats.update_one({"id": chat_id}, {"$set": {"archived": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}

@api_router.get("/chats/{chat_id}/export")
async def export_chat(chat_id: str):
    chat = await db.chats.find_one({"id": chat_id}, {"_id": 0})
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

class ChatImport(BaseModel):
    version: str = "1.0"
    chat: dict
    messages: list

@api_router.post("/chats/import")
async def import_chat(data: ChatImport):
    new_chat_id = str(uuid.uuid4())
    chat_data = {
        "id": new_chat_id,
        "title": data.chat.get("title", "Imported Chat"),
        "model": data.chat.get("model", "gpt-4o"),
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

@api_router.delete("/chats/archived/all")
async def delete_all_archived():
    archived = await db.chats.find({"archived": True}, {"id": 1, "_id": 0}).to_list(1000)
    for chat in archived:
        await db.messages.delete_many({"chat_id": chat["id"]})
    await db.chats.delete_many({"archived": True})
    return {"status": "ok", "deleted_count": len(archived)}

# ===== Settings Endpoints =====

@api_router.get("/settings")
async def get_settings():
    doc = await db.app_settings.find_one({"_id": "global"}, {"_id": 0})
    return doc or {}

@api_router.put("/settings")
async def update_settings(data: dict):
    await db.app_settings.update_one(
        {"_id": "global"},
        {"$set": data},
        upsert=True
    )
    return {"status": "ok"}

# Include the router in the main app after all routes are defined
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()