"""
Secure token generation for email verification, password reset, and invitations.

Generates cryptographically secure random tokens, hashes them for storage,
and validates them against stored hashes. Uses secrets module for CSPRNG.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


class SecureTokenGenerator:
    """
    Generates and validates secure tokens for out-of-band flows.

    Tokens are generated as URL-safe random strings. For storage, the
    token is hashed (SHA-256) so the raw token is never persisted.
    """

    @classmethod
    def generate_token(cls, length: int = 64) -> str:
        """
        Generate a cryptographically secure random token.

        Args:
            length: The byte length of the token (default 64 bytes → 86 URL-safe chars).

        Returns:
            A URL-safe random token string.
        """
        return secrets.token_urlsafe(length)

    @classmethod
    def hash_token(cls, token: str) -> str:
        """
        Hash a token using SHA-256 for secure storage.

        Args:
            token: The raw token string to hash.

        Returns:
            The hex-encoded SHA-256 digest.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    def verify_token(cls, raw_token: str, hashed_token: str) -> bool:
        """
        Verify a raw token against its stored hash.

        Args:
            raw_token: The token provided by the user.
            hashed_token: The stored SHA-256 hash to compare against.

        Returns:
            ``True`` if the token matches, ``False`` otherwise.
        """
        return cls.hash_token(raw_token) == hashed_token

    @classmethod
    def is_token_expired(
        cls,
        expires_at: datetime | None,
        now: datetime | None = None,
    ) -> bool:
        """
        Check whether a token has expired.

        Args:
            expires_at: The token's expiration timestamp.
            now: The current time (defaults to UTC now).

        Returns:
            ``True`` if the token is expired, ``False`` otherwise.
        """
        if expires_at is None:
            return True
        check_time = now or datetime.now(timezone.utc)
        return check_time > expires_at

    @classmethod
    def generate_expires_at(
        cls,
        hours: int = 1,
        days: int = 0,
    ) -> datetime:
        """
        Generate a UTC expiration timestamp for a token.

        Args:
            hours: Number of hours from now.
            days: Number of days from now.

        Returns:
            A timezone-aware UTC datetime.
        """
        return datetime.now(timezone.utc) + timedelta(hours=hours, days=days)