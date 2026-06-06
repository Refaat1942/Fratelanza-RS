from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.security import verify_token
from app.models.tenant import Company, CompanySubscription
from app.models.users import User, UserStatus
from app.services.module_service import ModuleService


class ModuleGuardMiddleware(BaseHTTPMiddleware):
    """Block company API calls when the target module is disabled for that tenant."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        api_prefix = "/api/v1"
        if not path.startswith(api_prefix):
            return await call_next(request)

        relative = path[len(api_prefix) :]
        module_key = ModuleService.module_for_path(relative)
        if not module_key:
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return await call_next(request)

        token = auth.split(" ", 1)[1]
        payload = verify_token(token, "access")
        if not payload:
            return await call_next(request)

        async with AsyncSessionLocal() as db:
            user_id = int(payload["sub"])
            result = await db.execute(select(User).where(User.id == user_id, User.is_deleted == False))
            user = result.scalar_one_or_none()
            if not user or user.status == UserStatus.SUSPENDED:
                return await call_next(request)
            if user.is_super_admin or not user.company_id:
                return await call_next(request)

            company_result = await db.execute(
                select(Company)
                .options(selectinload(Company.subscription).selectinload(CompanySubscription.plan))
                .where(Company.id == user.company_id)
            )
            company = company_result.scalar_one_or_none()
            if not company:
                return await call_next(request)

            plan = company.subscription.plan if company.subscription else None
            if not ModuleService.is_enabled(company, module_key, plan):
                return JSONResponse(
                    status_code=403,
                    content={"detail": f"Module '{module_key}' is not enabled for your company"},
                )

        return await call_next(request)
