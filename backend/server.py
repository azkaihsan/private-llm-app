from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime
import os

from config import db, client, logger
from models import StatusCheck, StatusCheckCreate
from storage import init_storage

from routers import auth as auth_router
from routers import chats as chats_router
from routers import connections as connections_router
from routers import files as files_router
from routers import settings as settings_router

app = FastAPI()

# Main API router
api_router = APIRouter(prefix="/api")


# ===== Health / Status =====

@api_router.get("/")
async def root():
    return {"message": "Hello World"}


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.model_dump())
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    await db.status_checks.insert_one(doc)
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks


# ===== Include all routers =====
api_router.include_router(auth_router.router)
api_router.include_router(chats_router.router)
api_router.include_router(connections_router.router)
api_router.include_router(files_router.router)
api_router.include_router(settings_router.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    try:
        init_storage()
        logger.info("Object storage initialized successfully")
    except Exception as e:
        logger.error(f"Object storage init failed: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
