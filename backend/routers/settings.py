from fastapi import APIRouter

from config import db

router = APIRouter()


@router.get("/settings")
async def get_settings():
    doc = await db.app_settings.find_one({"_id": "global"}, {"_id": 0})
    return doc or {}


@router.put("/settings")
async def update_settings(data: dict):
    await db.app_settings.update_one({"_id": "global"}, {"$set": data}, upsert=True)
    return {"status": "ok"}
