"""User repository for authentication and permissions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fratelanza.domain.entities import Role, User
from fratelanza.infrastructure.repositories.base import SqlServerRepository


@dataclass(frozen=True)
class UserCredentialsRecord:
    user: User
    password_hash: str


class UserRepository(SqlServerRepository):
    """Read and update users stored in SQL Server."""

    def find_credentials_by_username(self, username: str) -> UserCredentialsRecord | None:
        """Load an active user with role and password hash."""
        with self.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    u.UserId,
                    u.Username,
                    u.DisplayName,
                    u.PasswordHash,
                    u.IsActive,
                    u.LastLoginAt,
                    r.RoleId,
                    r.RoleName,
                    p.PermissionKey
                FROM security.Users u
                INNER JOIN security.Roles r ON r.RoleId = u.RoleId
                LEFT JOIN security.RolePermissions rp ON rp.RoleId = r.RoleId
                LEFT JOIN security.Permissions p ON p.PermissionId = rp.PermissionId
                WHERE u.Username = ?
                ORDER BY p.PermissionKey
                """,
                username,
            )
            rows = cursor.fetchall()

        if not rows:
            return None

        first = rows[0]
        permissions = frozenset(row.PermissionKey for row in rows if row.PermissionKey)
        role = Role(id=first.RoleId, name=first.RoleName, permissions=permissions)
        user = User(
            id=first.UserId,
            username=first.Username,
            display_name=first.DisplayName,
            role=role,
            is_active=bool(first.IsActive),
            last_login_at=first.LastLoginAt,
        )
        return UserCredentialsRecord(user=user, password_hash=first.PasswordHash)

    def update_last_login(self, user_id: int, when: datetime) -> None:
        """Persist the last successful login timestamp."""
        with self.cursor() as cursor:
            cursor.execute(
                "UPDATE security.Users SET LastLoginAt = ?, UpdatedAt = ? WHERE UserId = ?",
                when,
                when,
                user_id,
            )

    def write_activity(
        self,
        *,
        user_id: int | None,
        activity_type: str,
        description: str,
        device_name: str | None = None,
    ) -> None:
        """Write a user activity log entry."""
        with self.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO security.UserActivityLogs
                    (UserId, ActivityType, Description, DeviceName)
                VALUES (?, ?, ?, ?)
                """,
                user_id,
                activity_type,
                description,
                device_name,
            )
