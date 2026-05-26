"""Password hashing and validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import hmac
import os
import re


PASSWORD_ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 390_000
SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Hash a password with PBKDF2-SHA256.

    The output format is compatible with long-term storage:
    ``algorithm$iterations$salt$hash``.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "$".join(
        [
            PASSWORD_ALGORITHM,
            str(iterations),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        ]
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    """Return True when ``password`` matches ``encoded_hash``."""
    try:
        algorithm, iterations_text, salt_text, hash_text = encoded_hash.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_text.encode("ascii"))
        expected = base64.b64decode(hash_text.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


@dataclass(frozen=True)
class PasswordPolicy:
    """Reusable password policy for users and future SaaS accounts."""

    min_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_number: bool = True
    require_symbol: bool = True

    def validate(self, password: str) -> list[str]:
        """Return validation errors; an empty list means the password is valid."""
        errors: list[str] = []
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters.")
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must include an uppercase letter.")
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must include a lowercase letter.")
        if self.require_number and not re.search(r"\d", password):
            errors.append("Password must include a number.")
        if self.require_symbol and not re.search(r"[^A-Za-z0-9]", password):
            errors.append("Password must include a symbol.")
        return errors
