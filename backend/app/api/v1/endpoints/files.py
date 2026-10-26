"""Tenant-isolated file storage.

* ``POST /api/v1/files`` stores an upload under ``tenants/<company_id>/<category>/``.
* ``GET /uploads/<path>`` serves files: branding logos are public; anything under
  ``tenants/<id>/`` or ``contracts/<id>/`` requires a bearer token of a user of that tenant.
"""

import os
import uuid
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_token
from app.models.users import User, UserStatus

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".xlsx", ".csv", ".docx"}
ALLOWED_CATEGORIES = {"expenses", "contracts", "owners", "units", "admin_expenses", "general"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
PROTECTED_ROOTS = ("tenants", "contracts")


def _storage_root() -> Path:
    return Path(settings.STORAGE_LOCAL_PATH).resolve()


@router.post("/api/v1/files")
async def upload_file(
    current_user: Annotated[User, Depends(get_company_user)],
    file: UploadFile = File(...),
    category: str = Form("general"),
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 10MB)")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    rel_dir = Path("tenants") / str(current_user.company_id) / category
    abs_dir = _storage_root() / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (abs_dir / name).write_bytes(content)
    return {"url": f"/uploads/{rel_dir.as_posix()}/{name}", "size": len(content), "original_name": file.filename}


async def _bearer_user(request: Request, db: AsyncSession) -> Optional[User]:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    payload = verify_token(auth.split(" ", 1)[1], "access")
    if not payload:
        return None
    user = (
        await db.execute(select(User).where(User.id == int(payload["sub"]), User.is_deleted == False))  # noqa: E712
    ).scalar_one_or_none()
    if not user or user.status == UserStatus.SUSPENDED:
        return None
    return user


@router.get("/uploads/{file_path:path}", include_in_schema=False)
async def serve_upload(file_path: str, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    root = _storage_root()
    target = (root / file_path).resolve()
    if root not in target.parents or not target.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    parts = Path(file_path).parts
    if parts and parts[0] in PROTECTED_ROOTS:
        if len(parts) < 3 or not parts[1].isdigit():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        user = await _bearer_user(request, db)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        if not user.is_super_admin and user.company_id != int(parts[1]):
            # Same response as a missing file — never confirm another tenant's file exists
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    elif len(parts) != 1 or not parts[0].startswith("logo_"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return FileResponse(os.fspath(target))
