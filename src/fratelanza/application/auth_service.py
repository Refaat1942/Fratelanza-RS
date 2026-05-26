"""Authentication use cases."""

from __future__ import annotations

from datetime import datetime, timezone
import platform

from fratelanza.application.session import UserSession
from fratelanza.core.exceptions import AuthenticationError
from fratelanza.core.security import verify_password
from fratelanza.infrastructure.repositories.user_repository import UserRepository


class AuthService:
    """Authenticate users and record security activity."""

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    def login(self, username: str, password: str) -> UserSession:
        """Authenticate a user by username and password."""
        normalized_username = username.strip()
        if not normalized_username or not password:
            raise AuthenticationError("Username and password are required.")

        record = self._user_repository.find_credentials_by_username(normalized_username)
        if record is None or not record.user.is_active:
            self._write_failed_attempt(normalized_username)
            raise AuthenticationError("Invalid username or password.")

        if not verify_password(password, record.password_hash):
            self._write_failed_attempt(normalized_username)
            raise AuthenticationError("Invalid username or password.")

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        self._user_repository.update_last_login(record.user.id, now)
        self._user_repository.write_activity(
            user_id=record.user.id,
            activity_type="login.success",
            description="User logged in successfully.",
            device_name=platform.node(),
        )
        return UserSession(user=record.user)

    def _write_failed_attempt(self, username: str) -> None:
        self._user_repository.write_activity(
            user_id=None,
            activity_type="login.failed",
            description=f"Failed login attempt for username '{username}'.",
            device_name=platform.node(),
        )
