import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

DOCUMENT_CATEGORIES = [
    {"key": "legal_contract", "name_en": "Legal Contracts", "name_ar": "عقود قانونية"},
    {"key": "permit", "name_en": "Permits & Licenses", "name_ar": "تصاريح وتراخيص"},
    {"key": "engineering_drawing", "name_en": "Engineering Drawings", "name_ar": "مخططات هندسية"},
    {"key": "insurance", "name_en": "Insurance", "name_ar": "تأمين"},
    {"key": "other", "name_en": "Other", "name_ar": "أخرى"},
]

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

EXTENSION_BY_MIME = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


def category_label(category: str, lang: str = "en") -> str:
    for item in DOCUMENT_CATEGORIES:
        if item["key"] == category:
            return item["name_ar"] if lang == "ar" else item["name_en"]
    return category


async def validate_upload(file: UploadFile) -> tuple[bytes, str, str]:
    if not file.content_type or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and image files (JPEG, PNG, WebP, GIF) are allowed",
        )
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB",
        )
    ext = EXTENSION_BY_MIME.get(file.content_type, "")
    if file.filename and "." in file.filename:
        ext = Path(file.filename).suffix.lower() or ext
    return content, file.content_type, ext


def company_documents_dir(company_id: int) -> Path:
    base = Path(settings.STORAGE_LOCAL_PATH) / "documents" / str(company_id)
    base.mkdir(parents=True, exist_ok=True)
    return base


async def save_document_file(company_id: int, file: UploadFile) -> tuple[str, str, int, str]:
    content, mime_type, ext = await validate_upload(file)
    filename = f"{uuid.uuid4().hex}{ext}"
    rel_path = f"documents/{company_id}/{filename}"
    abs_path = Path(settings.STORAGE_LOCAL_PATH) / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_path, "wb") as f:
        f.write(content)
    original = file.filename or filename
    return rel_path, mime_type, len(content), original


def resolve_document_path(file_path: str | None, file_url: str | None) -> Path | None:
    if file_path:
        return Path(settings.STORAGE_LOCAL_PATH) / file_path
    if file_url and file_url.startswith("/uploads/"):
        return Path(settings.STORAGE_LOCAL_PATH) / file_url.removeprefix("/uploads/")
    if file_url and not file_url.startswith("http"):
        return Path(settings.STORAGE_LOCAL_PATH) / file_url.lstrip("/")
    return None


def delete_document_file(file_path: str | None, file_url: str | None) -> None:
    path = resolve_document_path(file_path, file_url)
    if path and path.is_file():
        try:
            os.remove(path)
        except OSError:
            pass
