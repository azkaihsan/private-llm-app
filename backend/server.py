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
AVAILABLE_MODELS = [
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "size": ""},
    {"id": "gpt-4.1-mini", "name": "GPT-4.1 mini", "provider": "openai", "size": ""},
    {"id": "gpt-5.1", "name": "GPT-5.1", "provider": "openai", "size": ""},
    {"id": "gpt-5-mini", "name": "GPT-5 mini", "provider": "openai", "size": ""},
    {"id": "claude-sonnet-4-5-20250929", "name": "Claude Sonnet 4.5", "provider": "anthropic", "size": ""},
    {"id": "claude-4-sonnet-20250514", "name": "Claude 4 Sonnet", "provider": "anthropic", "size": ""},
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini", "size": ""},
    {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "gemini", "size": ""},
]

MODEL_PROVIDER_MAP = {m["id"]: m["provider"] for m in AVAILABLE_MODELS}

class ChatCreate(BaseModel):
    title: str = ""
    model: str = "gpt-4o"

class ChatUpdate(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str

# ===== Chat Endpoints =====

@api_router.get("/models")
async def get_models():
    return AVAILABLE_MODELS

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
    api_key = os.environ.get("EMERGENT_LLM_KEY", "")

    try:
        # Load custom system prompt from settings
        app_settings = await db.app_settings.find_one({"_id": "global"}, {"_id": 0})
        system_prompt = (app_settings or {}).get("systemPrompt", "You are a helpful AI assistant. You provide clear, accurate, and well-formatted responses using markdown when appropriate.")

        llm = LlmChat(
            api_key=api_key,
            session_id=chat_id,
            system_message=system_prompt
        ).with_model(provider, model_id)

        user_message = UserMessage(text=data.content)
        response_text = await llm.send_message(user_message)
    except Exception as e:
        print(f"LLM error: {e}")
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