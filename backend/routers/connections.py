from fastapi import APIRouter, Depends
import os
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

from config import db
from auth import get_admin_user
from models import TestConnectionRequest, ALL_MODELS, EMERGENT_PROVIDERS

router = APIRouter()


@router.get("/connections")
async def get_connections(admin=Depends(get_admin_user)):
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


@router.put("/connections")
async def update_connections(data: dict, admin=Depends(get_admin_user)):
    await db.connections.update_one({"_id": "global"}, {"$set": data}, upsert=True)
    return {"status": "ok"}


@router.post("/connections/test")
async def test_connection(data: TestConnectionRequest, admin=Depends(get_admin_user)):
    try:
        llm = LlmChat(
            api_key=data.apiKey,
            session_id=f"test-{uuid.uuid4()}",
            system_message="Reply with exactly: CONNECTION_OK"
        ).with_model(data.provider, None)
        await llm.send_message(UserMessage(text="Say CONNECTION_OK"))
        return {"status": "ok", "message": "Connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/models")
async def get_models():
    conn = await db.connections.find_one({"_id": "global"}, {"_id": 0})
    if not conn:
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

    compat_config = providers.get("openai_compatible", {})
    if compat_config.get("enabled", False) and compat_config.get("customModels", ""):
        custom_models = [m.strip() for m in compat_config["customModels"].split(",") if m.strip()]
        for cm in custom_models:
            model_entry = {"id": f"openai/{cm}", "name": cm, "provider": "openai_compatible", "enabled": f"openai/{cm}" not in disabled}
            result.append(model_entry)

    return result
