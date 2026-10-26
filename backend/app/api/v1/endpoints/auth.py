from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, log_audit
from app.core.database import get_db
from app.models.users import User
from app.schemas.auth import LoginRequest, PasswordChangeRequest, RefreshTokenRequest, TokenResponse, UserResponse
from app.core.security import get_password_hash, verify_password
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        tokens, user = await AuthService.login(db, data)
    except HTTPException as exc:
        # Recorded in a separate transaction: the request transaction is rolled back on errors
        from app.core.database import AsyncSessionLocal
        from app.models.system import AuditLog

        async with AsyncSessionLocal() as audit_db:
            audit_db.add(AuditLog(
                action="login_failed", module="auth",
                ip_address=request.client.host if request.client else None,
                user_agent=(request.headers.get("user-agent") or "")[:500],
                details=f"login={data.username.strip().lower()[:100]} reason={exc.detail}",
            ))
            await audit_db.commit()
        raise
    await log_audit(db, request, user, "login", "auth")
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await AuthService.refresh(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await AuthService.to_user_response_enriched(db, current_user)


@router.get("/me/permissions")
async def my_permissions(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Effective permissions of the caller — the frontend uses this only for display;
    every API call is authorised again on the server."""
    from app.api.deps import get_access
    from app.services.access_service import AccessService

    ctx = await get_access(request, db, current_user)
    demo = None
    if ctx.is_demo and current_user.company_id:
        d = await AccessService.load_demo(db, current_user.company_id)
        if d:
            demo = {"prospect_name": d.prospect_name, "expires_at": d.expires_at.isoformat() if d.expires_at else None,
                    "profile": d.profile}
    return {**ctx.to_dict(), "demo": demo}


@router.post("/change-password")
async def change_password(
    data: PasswordChangeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.password_hash = get_password_hash(data.new_password)
    await db.flush()
    return {"message": "Password changed successfully", "success": True}


@router.post("/logout")
async def logout(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await log_audit(db, request, current_user, "logout", "auth")
    return {"message": "Logged out successfully", "success": True}
