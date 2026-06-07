"""Security headers and basic rate limiting."""

import time
from collections import defaultdict
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# In-memory login attempt tracking (per IP + username)
_login_attempts: dict[str, list[float]] = defaultdict(list)
_login_lock = Lock()
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 900  # 15 minutes


def record_login_failure(key: str) -> int:
    """Record a failed login attempt. Returns current attempt count in window."""
    now = time.time()
    with _login_lock:
        attempts = _login_attempts[key]
        attempts[:] = [t for t in attempts if now - t < _WINDOW_SECONDS]
        attempts.append(now)
        return len(attempts)


def clear_login_attempts(key: str) -> None:
    with _login_lock:
        _login_attempts.pop(key, None)


def is_login_blocked(key: str, max_attempts: int = _MAX_ATTEMPTS) -> bool:
    now = time.time()
    with _login_lock:
        attempts = _login_attempts.get(key, [])
        recent = [t for t in attempts if now - t < _WINDOW_SECONDS]
        return len(recent) >= max_attempts


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Block brute-force login attempts by IP."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "POST" and request.url.path.endswith("/auth/login"):
            client_ip = request.client.host if request.client else "unknown"
            if is_login_blocked(f"ip:{client_ip}"):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many login attempts. Please try again later."},
                )
        return await call_next(request)
