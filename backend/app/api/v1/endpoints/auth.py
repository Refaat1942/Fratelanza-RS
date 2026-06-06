from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.rbac import ROLE_PERMISSIONS
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models import User, UserStatus
from app.schemas import LoginRequest, Token, UserRead

router = APIRouter()


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    token = create_access_token(
        subject=user.id,
        claims={
            "company_id": user.company_id,
            "role": user.role.value,
            "locale": user.locale,
        },
    )
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    permissions = sorted(ROLE_PERMISSIONS.get(current_user.role, set()))
    return UserRead.model_validate(current_user).model_copy(update={"permissions": permissions})
