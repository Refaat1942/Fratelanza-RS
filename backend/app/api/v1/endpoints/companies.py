from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_company_user, get_super_admin
from app.core.database import get_db
from app.models.users import User
from app.schemas.company import BranchCreate, BranchResponse, CompanyResponse
from app.services.company_service import CompanyService
from app.models.tenant import Branch

router = APIRouter()


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.company_id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No company assigned")
    company = await CompanyService.get_company(db, current_user.company_id)
    return CompanyResponse.model_validate(company)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.is_super_admin and current_user.company_id != company_id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    company = await CompanyService.get_company(db, company_id)
    return CompanyResponse.model_validate(company)


@router.post("/{company_id}/branches", response_model=BranchResponse)
async def create_branch(
    company_id: int,
    data: BranchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_company_user)],
):
    if not current_user.is_super_admin and current_user.company_id != company_id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    branch = Branch(company_id=company_id, **data.model_dump())
    db.add(branch)
    await db.flush()
    return BranchResponse.model_validate(branch)
