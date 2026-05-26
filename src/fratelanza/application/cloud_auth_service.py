"""Cloud authentication for EXE-only deployments."""

from __future__ import annotations

from fratelanza.application.cloud_api_client import CloudApiClient
from fratelanza.application.session import UserSession
from fratelanza.core.exceptions import AuthenticationError
from fratelanza.domain.entities import Role, User


class CloudAuthService:
    """Authenticate users through the VPS API instead of local SQL Server."""

    def __init__(self, client: CloudApiClient) -> None:
        self._client = client

    def login(self, username: str, password: str) -> UserSession:
        """Authenticate a user against the VPS."""
        if not username.strip() or not password:
            raise AuthenticationError("Username and password are required.")
        try:
            payload = self._client.request(
                "POST",
                "/auth/login",
                {"username": username.strip(), "password": password},
            )
        except Exception as exc:
            raise AuthenticationError("Cloud login failed.") from exc

        role = Role(
            id=int(payload["role"]["id"]),
            name=str(payload["role"]["name"]),
            permissions=frozenset(payload["role"].get("permissions", [])),
        )
        user = User(
            id=int(payload["id"]),
            username=str(payload["username"]),
            display_name=str(payload["display_name"]),
            role=role,
            is_active=bool(payload.get("is_active", True)),
        )
        return UserSession(user=user)
