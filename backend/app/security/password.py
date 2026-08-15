"""
Password hashing, validation, and history management.

Uses bcrypt for password hashing with support for Argon2 as an alternative.
Provides password strength validation, history tracking, and expiration
checks per enterprise security standards.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

from app.config import settings


class PasswordManager:
    """
    Manages password hashing, verification, and policy enforcement.

    Uses a CryptContext that supports bcrypt (default) or Argon2.
    All methods are stateless and thread-safe.
    """

    _pwd_context = CryptContext(
        schemes=["bcrypt", "argon2"],
        default="bcrypt",
        bcrypt__rounds=12,
        deprecated="auto",
    )

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        """
        Hash a plain-text password using the configured algorithm.

        Args:
            plain_password: The raw password string.

        Returns:
            The hashed password string suitable for storage.
        """
        return cls._pwd_context.hash(plain_password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against its stored hash.

        Args:
            plain_password: The raw password to verify.
            hashed_password: The stored hash to compare against.

        Returns:
            ``True`` if the password matches, ``False`` otherwise.
        """
        return cls._pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def validate_password_strength(cls, password: str) -> tuple[bool, str]:
        """
        Validate a password against enterprise security policy.

        Checks:
            - Minimum length (configurable via ``PASSWORD_MIN_LENGTH``)
            - At least one uppercase letter
            - At least one lowercase letter
            - At least one digit
            - At least one special character

        Args:
            password: The password to validate.

        Returns:
            A tuple of ``(is_valid, error_message)``.
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return (
                False,
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long.",
            )

        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(
            r"[A-Z]", password
        ):
            return (False, "Password must contain at least one uppercase letter.")

        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(
            r"[a-z]", password
        ):
            return (False, "Password must contain at least one lowercase letter.")

        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", password):
            return (False, "Password must contain at least one digit.")

        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(
            r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\';/`~]", password
        ):
            return (
                False,
                "Password must contain at least one special character.",
            )

        return (True, "")

    @classmethod
    def is_password_expired(cls, password_changed_at: datetime | None) -> bool:
        """
        Check whether a password has exceeded its expiration period.

        Args:
            password_changed_at: The timestamp when the password was last changed.

        Returns:
            ``True`` if the password is expired, ``False`` otherwise.
        """
        if password_changed_at is None:
            return True
        expiration = password_changed_at + timedelta(
            days=settings.PASSWORD_EXPIRATION_DAYS
        )
        return datetime.now(timezone.utc) > expiration

    @classmethod
    def is_password_in_history(
        cls,
        plain_password: str,
        password_history: list[str],
    ) -> bool:
        """
        Check whether a password matches any recent password in history.

        Args:
            plain_password: The candidate password to check.
            password_history: List of previously hashed passwords.

        Returns:
            ``True`` if the password was used recently, ``False`` otherwise.
        """
        for old_hash in password_history:
            if cls.verify_password(plain_password, old_hash):
                return True
        return False