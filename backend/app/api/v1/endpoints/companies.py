from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.rbac import Permission, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Branch, Company, User, UserStatus
from app.schemas import BranchCreate, BranchRead, CompanyCreate, CompanyRead, UserCreate, UserRead

router = APIRouter()


@router.get("", response_model=list[CompanyRead])
def list_companies(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.COMPANIES_MANAGE)),
) -> list[Company]:
    return list(db.scalars(select(Company).order_by(Company.created_at.desc())))


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(Permission.COMPANIES_MANAGE)),
) -> Company:
    company = Company(**payload.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/branches", response_model=BranchRead, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
) -> Branch:
    if Permission.PLATFORM_ALL not in ROLE_PERMISSIONS[current_user.role]:
        if payload.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid tenant scope")

    branch = Branch(**payload.model_dump())
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


@router.get("/users", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
) -> list[UserRead]:
    query = select(User).order_by(User.created_at.desc())
    if Permission.PLATFORM_ALL not in ROLE_PERMISSIONS[current_user.role]:
        query = query.where(User.company_id == current_user.company_id)

    users = db.scalars(query).all()
    return [
        UserRead.model_validate(user).model_copy(
            update={"permissions": sorted(ROLE_PERMISSIONS.get(user.role, set()))}
        )
        for user in users
    ]


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USERS_MANAGE)),
) -> UserRead:
    role_permissions = ROLE_PERMISSIONS[current_user.role]
    company_id = payload.company_id
    if Permission.PLATFORM_ALL not in role_permissions:
        company_id = current_user.company_id
        if payload.company_id and payload.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid tenant scope")

    user = User(
        company_id=company_id,
        branch_id=payload.branch_id,
        full_name=payload.full_name,
        email=str(payload.email),
        mobile=payload.mobile,
        password_hash=hash_password(payload.password),
        role=payload.role,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserRead.model_validate(user).model_copy(
        update={"permissions": sorted(ROLE_PERMISSIONS.get(user.role, set()))}
    )
