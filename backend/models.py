from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid

# ===== Status Models =====

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# ===== Auth Models =====

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AdminCreateUser(BaseModel):
    name: str
    email: str
    password: str
    role: str = "user"

class AdminUpdateUser(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

# ===== Chat Models =====

class ChatCreate(BaseModel):
    title: str = ""
    model: str = "gpt-4o"

class ChatUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str
    file_ids: Optional[List[str]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None

class ChatImport(BaseModel):
    version: str = "1.0"
    chat: dict
    messages: list

# ===== Connection Models =====

class TestConnectionRequest(BaseModel):
    provider: str
    apiKey: str

# ===== LLM Model Definitions =====

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

EMERGENT_PROVIDERS = {"openai", "anthropic", "gemini"}

PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "grok": "https://api.x.ai/v1",
    "perplexity": "https://api.perplexity.ai",
}

FLAT_MODELS = [m for models in ALL_MODELS.values() for m in models]
MODEL_PROVIDER_MAP = {m["id"]: m["provider"] for m in FLAT_MODELS}
