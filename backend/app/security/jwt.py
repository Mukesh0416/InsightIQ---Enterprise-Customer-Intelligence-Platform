"""
JWT token management for authentication and authorization.

Provides creation, validation, and decoding of access and refresh tokens
using the python-jose library. Supports configurable expiration, issuer
validation, and claim extraction.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings


class JWTManager:
    """
    Manages JWT access and refresh token lifecycle.

    All tokens are signed using the configured algorithm and secret key.
    Access tokens are short-lived; refresh tokens have longer expiration.
    """

    @classmethod
    def create_access_token(
        cls,
        subject: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a signed JWT access token.

        Args:
            subject: The token subject (usually the user ID as string).
            extra_claims: Optional additional claims to include.

        Returns:
            The encoded JWT string.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "iss": settings.JWT_ISSUER,
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": str(uuid.uuid4()),
            "type": "access",
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @classmethod
    def create_refresh_token(cls, subject: str) -> str:
        """
        Create a signed JWT refresh token.

        Args:
            subject: The token subject (usually the user ID as string).

        Returns:
            The encoded JWT string.
        """
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "iss": settings.JWT_ISSUER,
            "iat": now,
            "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }
        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    @classmethod
    def decode_token(cls, token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT token.

        Args:
            token: The encoded JWT string.

        Returns:
            The decoded payload as a dictionary.

        Raises:
            JWTError: If the token is invalid, expired, or tampered with.
        """
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
        )

    @classmethod
    def get_subject(cls, token: str) -> str:
        """
        Extract the subject (user ID) from a valid token.

        Args:
            token: The encoded JWT string.

        Returns:
            The subject claim value.

        Raises:
            JWTError: If the token is invalid or the subject is missing.
        """
        payload = cls.decode_token(token)
        subject = payload.get("sub")
        if not subject:
            raise JWTError("Token missing 'sub' claim")
        return subject

    @classmethod
    def is_token_expired(cls, token: str) -> bool:
        """
        Check whether a token has expired.

        Args:
            token: The encoded JWT string.

        Returns:
            ``True`` if the token is expired, ``False`` otherwise.
        """
        try:
            cls.decode_token(token)
            return False
        except JWTError:
            return True

    @classmethod
    def get_token_type(cls, token: str) -> str | None:
        """
        Extract the ``type`` claim from a token.

        Args:
            token: The encoded JWT string.

        Returns:
            The token type ('access' or 'refresh') or ``None``.
        """
        try:
            payload = cls.decode_token(token)
            return payload.get("type")
        except JWTError:
            return None