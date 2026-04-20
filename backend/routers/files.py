from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import Response
from datetime import datetime, timezone
import uuid

from config import db
from auth import get_current_user, get_optional_user, decode_token
from storage import put_object, get_object, is_image_file, APP_NAME, MAX_FILE_SIZE

router = APIRouter()


@router.post("/files/upload")
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "bin"
    file_id = str(uuid.uuid4())
    storage_path = f"{APP_NAME}/uploads/{user['id']}/{file_id}.{ext}"
    content_type = file.content_type or "application/octet-stream"

    result = put_object(storage_path, data, content_type)

    file_doc = {
        "id": file_id,
        "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": content_type,
        "size": len(data),
        "user_id": user["id"],
        "is_image": is_image_file(file.filename, content_type),
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.files.insert_one({**file_doc, "_id": file_id})
    return {k: v for k, v in file_doc.items() if k != "_id"}


@router.get("/files/{file_id}")
async def download_file(file_id: str, auth: str = Query(None), user=Depends(get_optional_user)):
    if not user and auth:
        try:
            payload = decode_token(auth)
            user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        except Exception:
            pass
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    record = await db.files.find_one({"id": file_id, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    data, ct = get_object(record["storage_path"])
    return Response(content=data, media_type=record.get("content_type", ct))
