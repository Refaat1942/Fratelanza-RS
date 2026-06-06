import json
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user
from app.core.database import get_db
from app.models.customers import ActivityType, Customer, CustomerActivity
from app.models.crm import Lead, LeadSource, LeadStage
from app.models.users import User
from app.schemas.common import PaginatedResponse
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.user import ClientOnboard
from app.services.ai_service import AIService
from app.services.customer_import_service import CUSTOMER_FIELDS, CustomerImportService
from app.services.export_service import ExportService

router = APIRouter()


class ImportConfirmRequest(BaseModel):
    session_id: Optional[str] = None
    rows: Optional[list[dict[str, Any]]] = None
    duplicate_strategy: str = "skip"
    create_leads: bool = False
    default_source: str = "walk_in"


@router.get("/import/template")
async def download_import_template(
    current_user: Annotated[User, Depends(get_company_user)],
    format: str = Query("xlsx", pattern="^(csv|xlsx)$"),
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    rows = CustomerImportService.get_template_rows()
    filename = "customer_import_template"
    if format == "xlsx":
        content, fname = ExportService.to_excel(rows, f"{filename}.xlsx")
        return Response(
            content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={fname}"},
        )
    content, fname = ExportService.to_csv(rows, f"{filename}.csv")
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={fname}"})


@router.get("/import/fields")
async def import_field_reference(
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    from app.services.customer_import_service import FIELD_ALIASES
    return {
        "fields": CUSTOMER_FIELDS,
        "aliases": FIELD_ALIASES,
    }


@router.post("/import/preview")
async def preview_customer_import(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(None),
):
    """Smart preview: auto-detect columns from any company's export format."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    override = None
    if column_mapping:
        try:
            override = json.loads(column_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid column_mapping JSON")

    result = CustomerImportService.preview_file(content, file.filename or "upload.csv", override)
    if result.get("error"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    result["rows"] = await CustomerImportService.check_duplicates(
        db, current_user.company_id, result["rows"]
    )
    dupes = sum(1 for r in result["rows"] if r["status"] == "duplicate")
    result["summary"]["duplicates"] = dupes
    result["summary"]["valid"] = sum(1 for r in result["rows"] if r["status"] == "valid")
    return result


@router.post("/import/confirm")
async def confirm_customer_import(
    data: ImportConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")

    rows = data.rows
    if data.session_id and not rows:
        session = CustomerImportService.get_session(data.session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import session expired — upload again")
        rows = session["rows"]

    if not rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No rows to import")

    importable = [r for r in rows if r.get("status") in ("valid", "duplicate")]
    if data.duplicate_strategy == "skip":
        importable = [r for r in importable if r.get("status") != "duplicate"]

    return await CustomerImportService.confirm_import(
        db,
        current_user.company_id,
        current_user,
        importable,
        duplicate_strategy=data.duplicate_strategy,
        create_leads=data.create_leads,
        default_source=data.default_source,
    )


@router.post("/onboard", response_model=CustomerResponse)
async def onboard_client(
    data: ClientOnboard,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    """Odoo-style quick client registration with optional lead creation."""
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    customer = Customer(
        company_id=current_user.company_id,
        full_name_ar=data.full_name_ar,
        full_name_en=data.full_name_en,
        mobile=data.mobile,
        email=data.email,
        whatsapp=data.whatsapp,
        city=data.city,
        national_id=data.national_id,
        notes=data.notes,
        assigned_to_id=current_user.id,
    )
    db.add(customer)
    await db.flush()

    db.add(
        CustomerActivity(
            customer_id=customer.id,
            activity_type=ActivityType.NOTE,
            title="Client registered",
            description="New client onboarded via quick registration",
            created_by_id=current_user.id,
        )
    )

    if data.create_lead:
        try:
            source = LeadSource(data.source)
        except ValueError:
            source = LeadSource.WALK_IN
        lead = Lead(
            company_id=current_user.company_id,
            customer_id=customer.id,
            full_name=data.full_name_en,
            mobile=data.mobile,
            email=data.email,
            source=source,
            stage=LeadStage.NEW,
            assigned_to_id=current_user.id,
            notes=data.notes,
        )
        score, ai_score, qual = AIService.score_lead(lead)
        lead.score = score
        lead.ai_score = ai_score
        lead.ai_qualification = qual
        db.add(lead)

    await db.flush()
    return CustomerResponse.model_validate(customer)


@router.get("", response_model=PaginatedResponse[CustomerResponse])
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
):
    if not current_user.company_id and not current_user.is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    query = select(Customer).where(Customer.is_deleted == False)
    if not current_user.is_super_admin:
        query = query.where(Customer.company_id == current_user.company_id)
    if search:
        query = query.where(
            or_(
                Customer.full_name_ar.ilike(f"%{search}%"),
                Customer.full_name_en.ilike(f"%{search}%"),
                Customer.mobile.ilike(f"%{search}%"),
            )
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size))
    customers = result.scalars().all()
    pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        items=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=CustomerResponse)
async def create_customer(
    data: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company required")
    customer = Customer(company_id=current_user.company_id, **data.model_dump())
    db.add(customer)
    await db.flush()
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if not current_user.is_super_admin and customer.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id, Customer.is_deleted == False))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if not current_user.is_super_admin and customer.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    await db.flush()
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}/timeline")
async def get_customer_timeline(
    customer_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    result = await db.execute(
        select(CustomerActivity)
        .where(CustomerActivity.customer_id == customer_id)
        .order_by(CustomerActivity.created_at.desc())
    )
    activities = result.scalars().all()
    return [
        {
            "id": a.id,
            "activity_type": a.activity_type.value,
            "title": a.title,
            "description": a.description,
            "created_at": str(a.created_at),
        }
        for a in activities
    ]
