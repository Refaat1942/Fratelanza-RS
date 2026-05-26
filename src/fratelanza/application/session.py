"""Authenticated session state."""

from __future__ import annotations

from dataclasses import dataclass

from fratelanza.domain.entities import User


@dataclass(frozen=True)
class UserSession:
    """Current authenticated desktop session."""

    user: User

    @property
    def permissions(self) -> set[str]:
        return set(self.user.role.permissions)
