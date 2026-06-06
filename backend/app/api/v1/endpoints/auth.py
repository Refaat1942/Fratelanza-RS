from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, log_audit
from app.core.database import get_db
from app.models.users import User
from app.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tokens, user = await AuthService.login(db, data)
    await log_audit(db, request, user, "login", "auth")
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService.refresh(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return AuthService.to_user_response(current_user)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await log_audit(db, request, current_user, "logout", "auth")
    return {"message": "Logged out successfully", "success": True}
