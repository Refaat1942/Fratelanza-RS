"""Central server-side authorization for every company API call.

For each authenticated request this middleware resolves:
  * the tenant (from the user record — never from client input),
  * demo status (disabled / revoked / expired demos are rejected),
  * the module the path belongs to (feature flag),
  * the action implied by the HTTP method and path (view/create/edit/delete/approve/...),
and rejects the call with 403 unless the user's effective permissions allow it.

Endpoints still enforce record-level tenant ownership and data scope themselves.
"""

import re
from contextvars import ContextVar
from typing import Optional

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.database import AsyncSessionLocal
from app.core.security import verify_token
from app.models.users import User, UserStatus
from app.services.access_service import AccessContext, AccessService
from app.services.module_service import ModuleService

# Tenant context of the current request — read by the outbound gateway / AI client to keep
# demo tenants from reaching external services.
current_access: ContextVar[Optional[AccessContext]] = ContextVar("current_access", default=None)

# Self-service portals authorise by role inside the endpoint; only the feature flag applies here.
SELF_SERVICE_PREFIXES = ("/broker-portal", "/customer-portal")

# POST endpoints that only compute / read data
READ_ONLY_POSTS = (
    re.compile(r"^/collections/calculator/(preview|recalculate)$"),
    re.compile(r"^/(reports/)?ai/"),
    re.compile(r"^/ai/"),
)

# (regex on path, method or None for any, action)
ACTION_RULES: list[tuple[re.Pattern, Optional[str], str]] = [
    (re.compile(r"^/exports(/|$)"), None, "export"),
    (re.compile(r"/export$"), None, "export"),
    (re.compile(r"/(pdf|generate-pdf|statement|receipt|print)$"), None, "print"),
    (re.compile(r"^/roles(/|$)"), "WRITE", "manage_permissions"),
    (re.compile(r"^/users/\d+/(roles|modules)$"), "WRITE", "manage_permissions"),
    (re.compile(r"/(approve|reject|waive|adjust-approve)$"), "POST", "approve"),
    (re.compile(r"/adjustments$"), "POST", "approve"),
    (re.compile(r"/cancel$"), "POST", "cancel"),
    (re.compile(r"/terminate$"), "POST", "terminate"),
    (re.compile(r"/refunds?$"), "POST", "refund"),
    (re.compile(r"/(payments|collect)$"), "POST", "collect"),
]

METHOD_ACTIONS = {"GET": "view", "HEAD": "view", "OPTIONS": "view", "POST": "create", "PUT": "edit", "PATCH": "edit", "DELETE": "delete"}


def resolve_action(method: str, path: str) -> str:
    method = method.upper()
    if method == "POST" and any(p.search(path) for p in READ_ONLY_POSTS):
        return "view"
    for pattern, rule_method, action in ACTION_RULES:
        if rule_method == "WRITE" and method in ("GET", "HEAD", "OPTIONS"):
            continue
        if rule_method not in (None, "WRITE") and rule_method != method:
            continue
        if pattern.search(path):
            return action
    return METHOD_ACTIONS.get(method, "view")


def _deny(code: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": code, **extra})


class AccessGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        api_prefix = "/api/v1"
        if not path.startswith(api_prefix):
            return await call_next(request)
        relative = path[len(api_prefix):] or "/"

        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return await call_next(request)
        payload = verify_token(auth.split(" ", 1)[1], "access")
        if not payload:
            return await call_next(request)  # endpoint dependency returns the 401

        async with AsyncSessionLocal() as db:
            user = (
                await db.execute(select(User).where(User.id == int(payload["sub"]), User.is_deleted == False))  # noqa: E712
            ).scalar_one_or_none()
            if not user or user.status == UserStatus.SUSPENDED:
                return await call_next(request)

            company = None
            demo = None
            if not user.is_super_admin and user.company_id:
                company = await AccessService.load_company(db, user.company_id)
                if company is not None and company.is_demo:
                    demo = await AccessService.load_demo(db, company.id)
                    reason = AccessService.demo_state(demo)
                    if reason:
                        return _deny(reason)
            ctx = await AccessService.build(db, user, company, demo)

        request.state.access = ctx
        token = current_access.set(ctx)
        try:
            if ctx.is_super_admin:
                return await call_next(request)

            module_key = ModuleService.module_for_path(relative)
            if not module_key:
                return await call_next(request)
            if module_key not in ctx.enabled_modules:
                return _deny(f"Module '{module_key}' is not enabled for your company", module=module_key)
            if relative.startswith(SELF_SERVICE_PREFIXES):
                return await call_next(request)

            action = resolve_action(request.method, relative)
            if not ctx.can(module_key, action):
                return _deny("permission_denied", module=module_key, action=action)
            return await call_next(request)
        finally:
            current_access.reset(token)


# Backwards-compatible name used by app.main
ModuleGuardMiddleware = AccessGuardMiddleware
