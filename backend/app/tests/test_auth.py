"""
Unit tests for JWT authentication, password security, and token management.
"""

from __future__ import annotations

import pytest
from jose import JWTError

from app.security.jwt import JWTManager
from app.security.password import PasswordManager
from app.security.tokens import SecureTokenGenerator


class TestPasswordManager:
    """Tests for password hashing and validation."""

    def test_hash_and_verify_password(self) -> None:
        plain = "StrongPass!1"
        hashed = PasswordManager.hash_password(plain)
        assert hashed != plain
        assert PasswordManager.verify_password(plain, hashed)

    def test_verify_wrong_password(self) -> None:
        hashed = PasswordManager.hash_password("Correct!1")
        assert not PasswordManager.verify_password("Wrong!1", hashed)

    def test_password_strength_valid(self) -> None:
        is_valid, error = PasswordManager.validate_password_strength("Str0ng!Pass")
        assert is_valid is True
        assert error == ""

    def test_password_strength_short(self) -> None:
        is_valid, _ = PasswordManager.validate_password_strength("Ab1!")
        assert is_valid is False

    def test_password_strength_no_uppercase(self) -> None:
        is_valid, _ = PasswordManager.validate_password_strength("alllower1!")
        assert is_valid is False

    def test_password_strength_no_digit(self) -> None:
        is_valid, _ = PasswordManager.validate_password_strength("NoDigits!")
        assert is_valid is False

    def test_password_strength_no_special(self) -> None:
        is_valid, _ = PasswordManager.validate_password_strength("NoSpecial1")
        assert is_valid is False

    def test_password_history(self) -> None:
        old_hash = PasswordManager.hash_password("OldPass!1")
        assert PasswordManager.is_password_in_history("OldPass!1", [old_hash])
        assert not PasswordManager.is_password_in_history("NewPass!1", [old_hash])


class TestJWTManager:
    """Tests for JWT token creation and validation."""

    def test_create_and_decode_access_token(self) -> None:
        token = JWTManager.create_access_token("user-123")
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_create_and_decode_refresh_token(self) -> None:
        token = JWTManager.create_refresh_token("user-123")
        payload = JWTManager.decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_get_subject(self) -> None:
        token = JWTManager.create_access_token("user-456")
        assert JWTManager.get_subject(token) == "user-456"

    def test_get_token_type(self) -> None:
        access = JWTManager.create_access_token("user-1")
        refresh = JWTManager.create_refresh_token("user-1")
        assert JWTManager.get_token_type(access) == "access"
        assert JWTManager.get_token_type(refresh) == "refresh"

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(JWTError):
            JWTManager.decode_token("invalid.token.here")


class TestSecureTokenGenerator:
    """Tests for secure token generation and verification."""

    def test_generate_token_is_unique(self) -> None:
        t1 = SecureTokenGenerator.generate_token()
        t2 = SecureTokenGenerator.generate_token()
        assert t1 != t2
        assert len(t1) > 32

    def test_hash_and_verify_token(self) -> None:
        raw = SecureTokenGenerator.generate_token()
        hashed = SecureTokenGenerator.hash_token(raw)
        assert SecureTokenGenerator.verify_token(raw, hashed)
        assert not SecureTokenGenerator.verify_token("wrong-token", hashed)

    def test_is_token_expired(self) -> None:
        from datetime import datetime, timedelta, timezone

        past = datetime.now(timezone.utc) - timedelta(hours=1)
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        assert SecureTokenGenerator.is_token_expired(past)
        assert not SecureTokenGenerator.is_token_expired(future)
        assert SecureTokenGenerator.is_token_expired(None)