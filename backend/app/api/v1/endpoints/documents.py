from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.system import Document
from app.models.users import User
from app.services.document_service import (
    DOCUMENT_CATEGORIES,
    category_label,
    delete_document_file,
    resolve_document_path,
    save_document_file,
)

router = APIRouter()


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    project_id: Optional[int] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    is_archived: Optional[bool] = None


def _doc_dict(doc: Document) -> dict:
    return {
        "id": doc.id,
        "name": doc.name,
        "name_ar": doc.name_ar,
        "name_en": doc.name_en,
        "description": doc.description,
        "category": doc.category,
        "category_label_en": category_label(doc.category, "en"),
        "category_label_ar": category_label(doc.category, "ar"),
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "original_filename": doc.original_filename,
        "project_id": doc.project_id,
        "entity_type": doc.entity_type,
        "entity_id": doc.entity_id,
        "version": doc.version,
        "is_archived": doc.is_archived,
        "uploaded_by_id": doc.uploaded_by_id,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "is_image": (doc.file_type or "").startswith("image/"),
        "is_pdf": doc.file_type == "application/pdf",
    }


@router.get("/categories")
async def list_categories():
    return DOCUMENT_CATEGORIES


@router.get("/summary")
async def documents_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    base = select(Document.category, func.count(Document.id)).where(
        Document.company_id == current_user.company_id,
        Document.is_archived == False,
    ).group_by(Document.category)
    rows = (await db.execute(base)).all()
    counts = {cat: count for cat, count in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "by_category": counts,
        "categories": DOCUMENT_CATEGORIES,
    }


@router.get("")
async def list_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    category: Optional[str] = None,
    project_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    include_archived: bool = False,
):
    query = select(Document).where(Document.company_id == current_user.company_id)
    if not current_user.is_super_admin and not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    if not include_archived:
        query = query.where(Document.is_archived == False)
    if category:
        query = query.where(Document.category == category)
    if project_id:
        query = query.where(Document.project_id == project_id)
    if entity_type:
        query = query.where(Document.entity_type == entity_type)
    if search:
        like = f"%{search}%"
        query = query.where(
            Document.name.ilike(like)
            | Document.name_ar.ilike(like)
            | Document.name_en.ilike(like)
            | Document.original_filename.ilike(like)
        )
    query = query.order_by(Document.id.desc())
    docs = (await db.execute(query)).scalars().all()
    return [_doc_dict(d) for d in docs]


@router.post("")
async def upload_document(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form(...),
    name_ar: Optional[str] = Form(None),
    name_en: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    project_id: Optional[int] = Form(None),
    entity_type: Optional[str] = Form(None),
    entity_id: Optional[int] = Form(None),
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    valid_keys = {c["key"] for c in DOCUMENT_CATEGORIES}
    if category not in valid_keys:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")

    rel_path, mime_type, file_size, original = await save_document_file(current_user.company_id, file)
    doc = Document(
        company_id=current_user.company_id,
        name=name,
        name_ar=name_ar or name,
        name_en=name_en or name,
        description=description,
        file_url="",
        file_path=rel_path,
        original_filename=original,
        file_type=mime_type,
        file_size=file_size,
        category=category,
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        uploaded_by_id=current_user.id,
    )
    db.add(doc)
    await db.flush()
    doc.file_url = f"/api/v1/documents/{doc.id}/download"
    await db.flush()
    return _doc_dict(doc)


@router.get("/{document_id}")
async def get_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    doc = await _get_company_document(db, document_id, current_user)
    return _doc_dict(doc)


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    doc = await _get_company_document(db, document_id, current_user)
    path = resolve_document_path(doc.file_path, doc.file_url)
    if not path or not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on server")
    filename = doc.original_filename or path.name
    return FileResponse(
        path,
        media_type=doc.file_type or "application/octet-stream",
        filename=filename,
    )


@router.put("/{document_id}")
async def update_document(
    document_id: int,
    data: DocumentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    doc = await _get_company_document(db, document_id, current_user)
    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "category" and value not in {c["key"] for c in DOCUMENT_CATEGORIES}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")
        setattr(doc, field, value)
    await db.flush()
    return _doc_dict(doc)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    permanent: bool = False,
):
    doc = await _get_company_document(db, document_id, current_user)
    if permanent:
        delete_document_file(doc.file_path, doc.file_url)
        await db.delete(doc)
    else:
        doc.is_archived = True
    await db.flush()
    return {"success": True, "message": "Document removed"}


async def _get_company_document(db: AsyncSession, document_id: int, user: User) -> Document:
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not user.is_super_admin and doc.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return doc
