from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
import os
import re
import logging
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage
import litellm
import jwt
import bcrypt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# ===== Auth Config =====
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
security = HTTPBearer(auto_error=False)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_token(user_id: str, role: str) -> str:
    payload = {"sub": user_id, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    user = await db.users.find_one({"id": payload.get("sub")}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def get_admin_user(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def public_user(u: dict) -> dict:
    return {"id": u["id"], "name": u["name"], "email": u["email"], "role": u["role"], "created_at": u.get("created_at")}


def validate_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_RX.match(v) or len(v) > 254:
        raise ValueError("Invalid email address")
    return v


def validate_password(v: str) -> str:
    if len(v) < 6:
        raise ValueError("Password must be at least 6 characters")
    if len(v.encode("utf-8")) > 72:
        raise ValueError("Password is too long (max 72 bytes)")
    return v


def validate_name(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Name cannot be empty")
    if len(v) > 60:
        raise ValueError("Name is too long (max 60 characters)")
    return v


def sanitize_doc(data: dict, allowed: Optional[set] = None) -> dict:
    """Drop Mongo-unsafe keys ($-prefixed, dotted, _id) and, if given, keys outside the allowlist."""
    clean = {}
    for k, v in data.items():
        if not isinstance(k, str) or k.startswith("$") or "." in k or k == "_id":
            continue
        if allowed is not None and k not in allowed:
            continue
        clean[k] = v
    return clean


async def check_lockout(identifier: str):
    doc = await db.login_attempts.find_one({"identifier": identifier})
    if doc and doc.get("count", 0) >= MAX_LOGIN_ATTEMPTS:
        locked_until = datetime.fromisoformat(doc["locked_until"])
        if datetime.now(timezone.utc) < locked_until:
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in a few minutes.")
        await db.login_attempts.delete_one({"identifier": identifier})


async def record_failed_login(identifier: str):
    await db.login_attempts.update_one(
        {"identifier": identifier},
        {"$inc": {"count": 1}, "$set": {"locked_until": (datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()}},
        upsert=True,
    )


# ===== Lifespan: indexes + admin seeding =====
@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.chats.create_index([("user_id", 1), ("archived", 1), ("created_at", -1)])
    await db.chats.create_index("id", unique=True)
    await db.messages.create_index([("chat_id", 1), ("timestamp", 1)])
    await db.login_attempts.create_index("identifier", unique=True)

    admin_email = os.environ["ADMIN_EMAIL"].strip().lower()
    admin_password = os.environ["ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        uid = str(uuid.uuid4())
        await db.users.insert_one({
            "_id": uid, "id": uid, "name": "Admin", "email": admin_email,
            "password_hash": hash_password(admin_password), "role": "admin", "created_at": now_iso(),
        })
        logger.info("Seeded default admin user")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password), "role": "admin"}})
    yield
    client.close()


app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Open WebUI Clone API"}


# ===== Auth Endpoints =====

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    _v_name = field_validator("name")(classmethod(lambda cls, v: validate_name(v)))
    _v_email = field_validator("email")(classmethod(lambda cls, v: validate_email(v)))
    _v_pw = field_validator("password")(classmethod(lambda cls, v: validate_password(v)))


class LoginRequest(BaseModel):
    email: str
    password: str = Field(max_length=256)


@api_router.post("/auth/signup")
async def signup(data: SignupRequest):
    if await db.users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    role = "admin" if await db.users.count_documents({}) == 0 else "user"
    user = {"id": str(uuid.uuid4()), "name": data.name, "email": data.email, "password_hash": hash_password(data.password), "role": role, "created_at": now_iso()}
    await db.users.insert_one({**user, "_id": user["id"]})
    return {"token": create_token(user["id"], role), "user": public_user(user)}


@api_router.post("/auth/login")
async def login(data: LoginRequest):
    email = data.email.strip().lower()
    identifier = email
    await check_lockout(identifier)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user["password_hash"]):
        await record_failed_login(identifier)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await db.login_attempts.delete_one({"identifier": identifier})
    return {"token": create_token(user["id"], user["role"]), "user": public_user(user)}


@api_router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return user


class ProfileUpdate(BaseModel):
    name: str
    _v_name = field_validator("name")(classmethod(lambda cls, v: validate_name(v)))


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=256)
    new_password: str
    _v_pw = field_validator("new_password")(classmethod(lambda cls, v: validate_password(v)))


@api_router.put("/auth/profile")
async def update_profile(data: ProfileUpdate, user=Depends(get_current_user)):
    await db.users.update_one({"id": user["id"]}, {"$set": {"name": data.name}})
    return await db.users.find_one({"id": user["id"]}, {"_id": 0, "password_hash": 0})


@api_router.put("/auth/password")
async def change_password(data: PasswordChange, user=Depends(get_current_user)):
    full = await db.users.find_one({"id": user["id"]})
    if not full or not verify_password(data.current_password, full["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_password(data.new_password)}})
    return {"success": True}


# ===== Admin: User Management =====

class AdminCreateUser(BaseModel):
    name: str
    email: str
    password: str
    role: Literal["admin", "user"] = "user"
    _v_name = field_validator("name")(classmethod(lambda cls, v: validate_name(v)))
    _v_email = field_validator("email")(classmethod(lambda cls, v: validate_email(v)))
    _v_pw = field_validator("password")(classmethod(lambda cls, v: validate_password(v)))


class AdminUpdateUser(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Literal["admin", "user"]] = None
    password: Optional[str] = None
    _v_name = field_validator("name")(classmethod(lambda cls, v: validate_name(v) if v is not None else v))
    _v_email = field_validator("email")(classmethod(lambda cls, v: validate_email(v) if v is not None else v))
    _v_pw = field_validator("password")(classmethod(lambda cls, v: validate_password(v) if v is not None else v))


@api_router.get("/admin/users")
async def admin_list_users(admin=Depends(get_admin_user)):
    return await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(1000)


@api_router.post("/admin/users")
async def admin_create_user(data: AdminCreateUser, admin=Depends(get_admin_user)):
    if await db.users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = {"id": str(uuid.uuid4()), "name": data.name, "email": data.email, "password_hash": hash_password(data.password), "role": data.role, "created_at": now_iso()}
    await db.users.insert_one({**user, "_id": user["id"]})
    return public_user(user)


@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, data: AdminUpdateUser, admin=Depends(get_admin_user)):
    update = {}
    if data.name is not None:
        update["name"] = data.name
    if data.email is not None:
        if await db.users.find_one({"email": data.email, "id": {"$ne": user_id}}):
            raise HTTPException(status_code=400, detail="Email already in use")
        update["email"] = data.email
    if data.role is not None:
        if user_id == admin["id"] and data.role != "admin":
            raise HTTPException(status_code=400, detail="You cannot change your own role")
        update["role"] = data.role
    if data.password is not None:
        update["password_hash"] = hash_password(data.password)
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.users.update_one({"id": user_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin=Depends(get_admin_user)):
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    chat_ids = [c["id"] for c in await db.chats.find({"user_id": user_id}, {"id": 1}).to_list(10000)]
    if chat_ids:
        await db.messages.delete_many({"chat_id": {"$in": chat_ids}})
    await db.chats.delete_many({"user_id": user_id})
    return {"status": "ok"}


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

EMERGENT_PROVIDERS = {"openai", "anthropic", "gemini"}
PROVIDER_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "grok": "https://api.x.ai/v1",
    "perplexity": "https://api.perplexity.ai",
}
FLAT_MODELS = [m for models in ALL_MODELS.values() for m in models]
MODEL_PROVIDER_MAP = {m["id"]: m["provider"] for m in FLAT_MODELS}
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant. You provide clear, accurate, and well-formatted responses using markdown when appropriate."
DEFAULT_CONNECTIONS = {
    "providers": {
        "openai": {"enabled": True, "apiKey": "", "name": "OpenAI", "useEmergentKey": True},
        "anthropic": {"enabled": True, "apiKey": "", "name": "Anthropic", "useEmergentKey": True},
        "gemini": {"enabled": True, "apiKey": "", "name": "Google Gemini", "useEmergentKey": True},
        "deepseek": {"enabled": False, "apiKey": "", "name": "DeepSeek", "useEmergentKey": False, "baseUrl": PROVIDER_BASE_URLS["deepseek"]},
        "qwen": {"enabled": False, "apiKey": "", "name": "Qwen", "useEmergentKey": False, "baseUrl": PROVIDER_BASE_URLS["qwen"]},
        "grok": {"enabled": False, "apiKey": "", "name": "Grok (xAI)", "useEmergentKey": False, "baseUrl": PROVIDER_BASE_URLS["grok"]},
        "perplexity": {"enabled": False, "apiKey": "", "name": "Perplexity", "useEmergentKey": False, "baseUrl": PROVIDER_BASE_URLS["perplexity"]},
        "bedrock": {"enabled": False, "apiKey": "", "name": "Amazon Bedrock", "useEmergentKey": False, "awsRegion": "us-east-1", "awsAccessKey": "", "awsSecretKey": ""},
        "openai_compatible": {"enabled": False, "apiKey": "", "name": "OpenAI Compatible", "useEmergentKey": False, "baseUrl": "", "customModels": ""},
    },
    "defaultModel": "gpt-4o",
    "modelParams": {"temperature": 0.7, "maxTokens": 4096, "topP": 1.0},
    "disabledModels": [],
}
CONNECTION_KEYS = {"providers", "defaultModel", "modelParams", "disabledModels"}
SETTINGS_KEYS = {"appName", "logoType", "logoText", "logoImageUrl", "logoBgColor", "logoTextColor", "theme", "mainBg", "sidebarBg", "inputBg", "accentColor", "userBubbleBg", "fontSize", "systemPrompt"}
MAX_LOGO_BYTES = 700 * 1024


class ChatCreate(BaseModel):
    title: str = Field(default="", max_length=200)
    model: str = Field(default="gpt-4o", min_length=1, max_length=200)


class ChatUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        return v


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=32000)
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=128000)
    top_p: Optional[float] = Field(default=None, ge=0, le=1)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v


# ===== Connection & Model Endpoints =====

def emergent_key() -> str:
    return os.environ.get("EMERGENT_LLM_KEY", "")


@api_router.get("/connections")
async def get_connections(admin=Depends(get_admin_user)):
    doc = await db.connections.find_one({"_id": "global"}, {"_id": 0})
    return doc or DEFAULT_CONNECTIONS


@api_router.put("/connections")
async def update_connections(data: dict, admin=Depends(get_admin_user)):
    clean = sanitize_doc(data, CONNECTION_KEYS)
    if "providers" in clean:
        if not isinstance(clean["providers"], dict):
            raise HTTPException(status_code=400, detail="providers must be an object")
        clean["providers"] = {k: sanitize_doc(v) for k, v in clean["providers"].items() if k in DEFAULT_CONNECTIONS["providers"] and isinstance(v, dict)}
    if "disabledModels" in clean and not isinstance(clean["disabledModels"], list):
        raise HTTPException(status_code=400, detail="disabledModels must be a list")
    if "modelParams" in clean:
        if not isinstance(clean["modelParams"], dict):
            raise HTTPException(status_code=400, detail="modelParams must be an object")
        clean["modelParams"] = sanitize_doc(clean["modelParams"], {"temperature", "maxTokens", "topP"})
    if not clean:
        raise HTTPException(status_code=400, detail="No valid fields")
    await db.connections.update_one({"_id": "global"}, {"$set": clean}, upsert=True)
    return {"status": "ok"}


class TestConnectionRequest(BaseModel):
    provider: str = Field(max_length=50)
    apiKey: str = Field(default="", max_length=1000)


@api_router.post("/connections/test")
async def test_connection(data: TestConnectionRequest, admin=Depends(get_admin_user)):
    if data.provider not in ALL_MODELS:
        raise HTTPException(status_code=400, detail="Unknown provider")
    conn = await db.connections.find_one({"_id": "global"}, {"_id": 0}) or DEFAULT_CONNECTIONS
    prov_cfg = conn.get("providers", {}).get(data.provider, {})
    api_key = emergent_key() if data.apiKey in ("", "emergent") and data.provider in EMERGENT_PROVIDERS else data.apiKey
    try:
        if data.provider in EMERGENT_PROVIDERS:
            model_id = ALL_MODELS[data.provider][0]["id"]
            llm = LlmChat(api_key=api_key, session_id=f"test-{uuid.uuid4()}", system_message="Reply with exactly: OK").with_model(data.provider, model_id).with_params(max_tokens=5)
            await llm.send_message(UserMessage(text="Say OK"))
        else:
            models = ALL_MODELS[data.provider]
            if data.provider == "openai_compatible":
                custom = [m.strip() for m in (prov_cfg.get("customModels") or "").split(",") if m.strip()]
                if not custom:
                    return {"status": "error", "message": "Add at least one custom model name first"}
                model_id = f"openai/{custom[0]}"
            else:
                model_id = models[0]["id"]
            await litellm.acompletion(model=model_id, messages=[{"role": "user", "content": "Say OK"}], max_tokens=5, **provider_kwargs(data.provider, api_key, prov_cfg))
        return {"status": "ok", "message": "Connection successful"}
    except Exception as e:
        logger.warning(f"Connection test failed for {data.provider}: {e}")
        return {"status": "error", "message": str(e)[:300]}


def provider_kwargs(provider: str, api_key: str, cfg: dict) -> dict:
    if provider == "bedrock":
        return {"aws_access_key_id": cfg.get("awsAccessKey", ""), "aws_secret_access_key": cfg.get("awsSecretKey", ""), "aws_region_name": cfg.get("awsRegion", "us-east-1")}
    kwargs = {"api_key": api_key}
    if provider in ("qwen", "openai_compatible"):
        kwargs["api_base"] = cfg.get("baseUrl") or PROVIDER_BASE_URLS.get(provider, "")
    return kwargs


@api_router.get("/models")
async def get_models():
    conn = await db.connections.find_one({"_id": "global"}, {"_id": 0}) or DEFAULT_CONNECTIONS
    providers = conn.get("providers", {})
    disabled = set(conn.get("disabledModels", []))
    result = []
    for provider_key, models in ALL_MODELS.items():
        if provider_key == "openai_compatible":
            continue
        if providers.get(provider_key, {}).get("enabled", provider_key in EMERGENT_PROVIDERS):
            result.extend({**m, "enabled": m["id"] not in disabled} for m in models)
    compat = providers.get("openai_compatible", {})
    if compat.get("enabled", False) and compat.get("customModels", ""):
        for cm in [m.strip() for m in compat["customModels"].split(",") if m.strip()]:
            result.append({"id": f"openai/{cm}", "name": cm, "provider": "openai_compatible", "enabled": f"openai/{cm}" not in disabled})
    return result


# ===== Chat Endpoints =====

@api_router.get("/chats")
async def get_chats(user=Depends(get_current_user)):
    return await db.chats.find({"user_id": user["id"], "archived": {"$ne": True}}, {"_id": 0}).sort("created_at", -1).to_list(1000)


@api_router.post("/chats")
async def create_chat(data: ChatCreate, user=Depends(get_current_user)):
    chat = {"id": str(uuid.uuid4()), "title": data.title.strip() or "New Chat", "model": data.model, "user_id": user["id"], "created_at": now_iso(), "archived": False, "pinned": False}
    await db.chats.insert_one({**chat, "_id": chat["id"]})
    return chat


@api_router.get("/chats/archived")
async def get_archived_chats(user=Depends(get_current_user)):
    return await db.chats.find({"user_id": user["id"], "archived": True}, {"_id": 0}).sort("created_at", -1).to_list(1000)


@api_router.get("/chats/search")
async def search_chats(q: str, user=Depends(get_current_user)):
    term = q.strip()[:200]
    if len(term) < 2:
        return []
    rx = {"$regex": re.escape(term), "$options": "i"}
    chat_ids = [c["id"] for c in await db.chats.find({"user_id": user["id"], "archived": {"$ne": True}}, {"id": 1}).to_list(1000)]
    if not chat_ids:
        return []
    msgs = await db.messages.find({"chat_id": {"$in": chat_ids}, "content": rx}, {"_id": 0, "chat_id": 1, "content": 1, "role": 1}).to_list(1000)
    results = {}
    lower_term = term.lower()
    for m in msgs:
        if m["chat_id"] in results:
            results[m["chat_id"]]["count"] += 1
            continue
        content = m["content"]
        idx = content.lower().find(lower_term)
        start = max(0, idx - 40)
        end = idx + len(term) + 60
        snippet = ("…" if start > 0 else "") + content[start:end].replace("\n", " ") + ("…" if end < len(content) else "")
        results[m["chat_id"]] = {"chat_id": m["chat_id"], "snippet": snippet, "role": m["role"], "count": 1}
    return list(results.values())


@api_router.get("/chats/{chat_id}")
async def get_chat(chat_id: str, user=Depends(get_current_user)):
    chat = await db.chats.find_one({"id": chat_id, "user_id": user["id"]}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat["messages"] = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).to_list(2000)
    return chat


@api_router.put("/chats/{chat_id}")
async def update_chat(chat_id: str, data: ChatUpdate, user=Depends(get_current_user)):
    result = await db.chats.update_one({"id": chat_id, "user_id": user["id"]}, {"$set": {"title": data.title}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}


@api_router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str, user=Depends(get_current_user)):
    result = await db.chats.delete_one({"id": chat_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.messages.delete_many({"chat_id": chat_id})
    return {"status": "ok"}


async def set_chat_flag(chat_id: str, user_id: str, update: dict):
    result = await db.chats.update_one({"id": chat_id, "user_id": user_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "ok"}


@api_router.put("/chats/{chat_id}/pin")
async def pin_chat(chat_id: str, user=Depends(get_current_user)):
    return await set_chat_flag(chat_id, user["id"], {"pinned": True, "pinned_at": now_iso()})


@api_router.put("/chats/{chat_id}/unpin")
async def unpin_chat(chat_id: str, user=Depends(get_current_user)):
    return await set_chat_flag(chat_id, user["id"], {"pinned": False})


@api_router.put("/chats/{chat_id}/archive")
async def archive_chat(chat_id: str, user=Depends(get_current_user)):
    return await set_chat_flag(chat_id, user["id"], {"archived": True, "pinned": False})


@api_router.put("/chats/{chat_id}/unarchive")
async def unarchive_chat(chat_id: str, user=Depends(get_current_user)):
    return await set_chat_flag(chat_id, user["id"], {"archived": False})


@api_router.post("/chats/{chat_id}/messages")
async def send_message(chat_id: str, data: MessageCreate, user=Depends(get_current_user)):
    chat = await db.chats.find_one({"id": chat_id, "user_id": user["id"]}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    history = await db.messages.find({"chat_id": chat_id}, {"_id": 0, "role": 1, "content": 1}).sort("timestamp", -1).to_list(50)
    history.reverse()

    user_msg = {"id": str(uuid.uuid4()), "chat_id": chat_id, "role": "user", "content": data.content, "timestamp": now_iso()}
    await db.messages.insert_one({**user_msg, "_id": user_msg["id"]})

    if not history:
        title = data.content.strip()[:50] + ("..." if len(data.content.strip()) > 50 else "")
        await db.chats.update_one({"id": chat_id}, {"$set": {"title": title}})

    model_id = chat.get("model", "gpt-4o")
    provider = MODEL_PROVIDER_MAP.get(model_id)
    if provider is None:
        provider = "openai_compatible" if model_id.startswith("openai/") else "openai"

    conn = await db.connections.find_one({"_id": "global"}, {"_id": 0}) or DEFAULT_CONNECTIONS
    prov_config = conn.get("providers", {}).get(provider, {})
    if provider in EMERGENT_PROVIDERS and prov_config.get("useEmergentKey", True):
        api_key = emergent_key()
    else:
        api_key = prov_config.get("apiKey", "")
    model_params = conn.get("modelParams", {})
    temperature = data.temperature if data.temperature is not None else model_params.get("temperature", 0.7)
    max_tokens = data.max_tokens if data.max_tokens is not None else model_params.get("maxTokens", 4096)
    top_p = data.top_p if data.top_p is not None else model_params.get("topP", 1.0)

    try:
        app_settings = await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}
        system_prompt = app_settings.get("systemPrompt") or DEFAULT_SYSTEM_PROMPT
        messages_for_llm = [{"role": "system", "content": system_prompt}] + [{"role": h["role"], "content": h["content"]} for h in history]

        if provider in EMERGENT_PROVIDERS:
            llm = LlmChat(api_key=api_key, session_id=chat_id, system_message=system_prompt, initial_messages=messages_for_llm)
            llm.with_model(provider, model_id).with_params(temperature=temperature, max_tokens=max_tokens, top_p=top_p)
            response_text = await llm.send_message(UserMessage(text=data.content))
        else:
            response = await litellm.acompletion(
                model=model_id,
                messages=messages_for_llm + [{"role": "user", "content": data.content}],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                **provider_kwargs(provider, api_key, prov_config),
            )
            response_text = response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"LLM error for provider={provider} model={model_id}: {e}")
        response_text = "Sorry, I encountered an error while generating a response. Please try again."
        if user.get("role") == "admin":
            response_text += f"\n\n`{type(e).__name__}: {str(e)[:300]}`"

    ai_msg = {"id": str(uuid.uuid4()), "chat_id": chat_id, "role": "assistant", "content": response_text, "timestamp": now_iso()}
    await db.messages.insert_one({**ai_msg, "_id": ai_msg["id"]})
    return {"user_message": user_msg, "assistant_message": ai_msg}


# ===== Export / Import =====

@api_router.get("/chats/{chat_id}/export")
async def export_chat(chat_id: str, user=Depends(get_current_user)):
    chat = await db.chats.find_one({"id": chat_id, "user_id": user["id"]}, {"_id": 0})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = await db.messages.find({"chat_id": chat_id}, {"_id": 0}).sort("timestamp", 1).to_list(2000)
    return {"version": "1.0", "source": "open-webui-clone", "chat": chat, "messages": messages, "exported_at": now_iso()}


class ImportMessage(BaseModel):
    role: Literal["user", "assistant"] = "user"
    content: str = Field(default="", max_length=100000)
    timestamp: Optional[str] = Field(default=None, max_length=64)


class ChatImport(BaseModel):
    version: str = Field(default="1.0", max_length=20)
    chat: dict
    messages: List[ImportMessage] = Field(max_length=2000)


@api_router.post("/chats/import")
async def import_chat(data: ChatImport, user=Depends(get_current_user)):
    title = str(data.chat.get("title") or "Imported Chat").strip()[:200] or "Imported Chat"
    model = str(data.chat.get("model") or "gpt-4o")[:200]
    new_chat_id = str(uuid.uuid4())
    chat_data = {"id": new_chat_id, "title": title, "model": model, "user_id": user["id"], "created_at": now_iso(), "archived": False, "pinned": False}
    await db.chats.insert_one({**chat_data, "_id": new_chat_id})
    docs = []
    for i, msg in enumerate(data.messages):
        mid = str(uuid.uuid4())
        docs.append({"_id": mid, "id": mid, "chat_id": new_chat_id, "role": msg.role, "content": msg.content, "timestamp": msg.timestamp or (datetime.now(timezone.utc) + timedelta(milliseconds=i)).isoformat()})
    if docs:
        await db.messages.insert_many(docs)
    return {"status": "ok", "chat_id": new_chat_id, "chat": chat_data}


@api_router.delete("/chats/archived/all")
async def delete_all_archived(user=Depends(get_current_user)):
    archived_ids = [c["id"] for c in await db.chats.find({"user_id": user["id"], "archived": True}, {"id": 1, "_id": 0}).to_list(10000)]
    if archived_ids:
        await db.messages.delete_many({"chat_id": {"$in": archived_ids}})
        await db.chats.delete_many({"id": {"$in": archived_ids}, "user_id": user["id"]})
    return {"status": "ok", "deleted_count": len(archived_ids)}


# ===== Settings (global appearance) =====

@api_router.get("/settings")
async def get_settings():
    return await db.app_settings.find_one({"_id": "global"}, {"_id": 0}) or {}


@api_router.put("/settings")
async def update_settings(data: dict, admin=Depends(get_admin_user)):
    clean = sanitize_doc(data, SETTINGS_KEYS)
    if not clean:
        raise HTTPException(status_code=400, detail="No valid settings fields")
    logo = clean.get("logoImageUrl")
    if isinstance(logo, str) and len(logo) > MAX_LOGO_BYTES:
        raise HTTPException(status_code=400, detail="Logo image is too large (max 512KB)")
    if "fontSize" in clean:
        try:
            clean["fontSize"] = max(10, min(24, int(clean["fontSize"])))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="fontSize must be a number")
    if "systemPrompt" in clean and (not isinstance(clean["systemPrompt"], str) or len(clean["systemPrompt"]) > 8000):
        raise HTTPException(status_code=400, detail="systemPrompt must be a string under 8000 characters")
    await db.app_settings.update_one({"_id": "global"}, {"$set": clean}, upsert=True)
    return {"status": "ok"}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[o.strip() for o in os.environ.get('CORS_ORIGINS', '*').split(',') if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
