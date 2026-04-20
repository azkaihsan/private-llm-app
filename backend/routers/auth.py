from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from config import db
from auth import hash_password, verify_password, create_token, get_current_user, get_admin_user
from models import SignupRequest, LoginRequest, AdminCreateUser, AdminUpdateUser

router = APIRouter()


@router.post("/auth/signup")
async def signup(data: SignupRequest):
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_count = await db.users.count_documents({})
    role = "admin" if user_count == 0 else "user"

    user = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one({**user, "_id": user["id"]})
    token = create_token(user["id"], user["role"])
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]},
    }


@router.post("/auth/login")
async def login(data: LoginRequest):
    user = await db.users.find_one({"email": data.email.lower()})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"], user["role"])
    return {
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]},
    }


@router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    return user


# ===== Admin: User Management =====

@router.get("/admin/users")
async def admin_list_users(admin=Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)
    return users


@router.post("/admin/users")
async def admin_create_user(data: AdminCreateUser, admin=Depends(get_admin_user)):
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if data.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")

    user = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "role": data.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one({**user, "_id": user["id"]})
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"], "created_at": user["created_at"]}


@router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, data: AdminUpdateUser, admin=Depends(get_admin_user)):
    update = {}
    if data.name is not None:
        update["name"] = data.name
    if data.email is not None:
        existing = await db.users.find_one({"email": data.email.lower(), "id": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        update["email"] = data.email.lower()
    if data.role is not None:
        if data.role not in ("admin", "user"):
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
        update["role"] = data.role
    if data.password is not None:
        update["password_hash"] = hash_password(data.password)

    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.users.update_one({"id": user_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin=Depends(get_admin_user)):
    if admin["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    user_chats = await db.chats.find({"user_id": user_id}, {"id": 1}).to_list(1000)
    for chat in user_chats:
        await db.messages.delete_many({"chat_id": chat["id"]})
    await db.chats.delete_many({"user_id": user_id})
    return {"status": "ok"}
