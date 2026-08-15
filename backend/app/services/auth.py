"""Authentication service implementing all auth business logic."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.token import EmailVerificationToken, PasswordResetToken, RefreshToken
from app.models.user import User
from app.repositories.user import UserRepository
from app.security.jwt import JWTManager
from app.security.password import PasswordManager
from app.security.tokens import SecureTokenGenerator

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, email: str, password: str, first_name: str, last_name: str) -> User:
        is_valid, error = PasswordManager.validate_password_strength(password)
        if not is_valid:
            raise ValidationError(error)
        existing = await self.user_repo.find_by_email(email)
        if existing:
            raise ConflictError("A user with this email already exists.")
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=PasswordManager.hash_password(password),
            password_changed_at=datetime.now(timezone.utc),
        )
        created = await self.user_repo.create(user)
        logger.info("User registered: %s", email, extra={"extra_fields": {"user_id": str(created.id)}})
        return created

    async def login(self, email: str, password: str, ip_address: str | None = None) -> tuple[str, str, User]:
        user = await self.user_repo.find_by_email(email)
        if not user or not user.is_active:
            raise NotFoundError("Invalid email or password.")
        if user.is_locked:
            if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
                raise ValidationError("Account is temporarily locked. Try again later.")
            user.is_locked = False
            user.failed_login_attempts = 0
        if not PasswordManager.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.ACCOUNT_LOCKOUT_THRESHOLD:
                user.is_locked = True
                user.locked_until = datetime.now(timezone.utc)
            await self.session.flush()
            raise ValidationError("Invalid email or password.")
        user.failed_login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address
        await self.session.flush()
        access_token = JWTManager.create_access_token(str(user.id))
        refresh_token = JWTManager.create_refresh_token(str(user.id))
        await self._store_refresh_token(user.id, refresh_token)
        logger.info("User logged in: %s", email)
        return access_token, refresh_token, user

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        try:
            subject = JWTManager.get_subject(refresh_token)
            token_type = JWTManager.get_token_type(refresh_token)
            if token_type != "refresh":
                raise ValidationError("Invalid token type.")
        except Exception as e:
            raise ValidationError("Invalid or expired refresh token.") from e
        token_hash = SecureTokenGenerator.hash_token(refresh_token)
        stored = await self.session.execute(
            __import__("sqlalchemy").select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
            )
        )
        stored_token = stored.scalar_one_or_none()
        if not stored_token:
            raise ValidationError("Refresh token has been revoked.")
        stored_token.is_revoked = True
        stored_token.revoked_at = datetime.now(timezone.utc)
        new_access = JWTManager.create_access_token(subject)
        new_refresh = JWTManager.create_refresh_token(subject)
        await self._store_refresh_token(UUID(subject), new_refresh)
        await self.session.flush()
        return new_access, new_refresh

    async def logout(self, refresh_token: str) -> None:
        token_hash = SecureTokenGenerator.hash_token(refresh_token)
        result = await self.session.execute(
            __import__("sqlalchemy").select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
            )
        )
        stored = result.scalar_one_or_none()
        if stored:
            stored.is_revoked = True
            stored.revoked_at = datetime.now(timezone.utc)
            await self.session.flush()
            logger.info("Refresh token revoked")

    async def forgot_password(self, email: str) -> str:
        user = await self.user_repo.find_by_email(email)
        if not user:
            return "If the email exists, a reset link has been sent."
        raw_token = SecureTokenGenerator.generate_token()
        token_hash = SecureTokenGenerator.hash_token(raw_token)
        reset = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=SecureTokenGenerator.generate_expires_at(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
        )
        self.session.add(reset)
        await self.session.flush()
        logger.info("Password reset token generated for: %s", email)
        return raw_token

    async def reset_password(self, token: str, new_password: str) -> None:
        is_valid, error = PasswordManager.validate_password_strength(new_password)
        if not is_valid:
            raise ValidationError(error)
        token_hash = SecureTokenGenerator.hash_token(token)
        result = await self.session.execute(
            __import__("sqlalchemy").select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.is_used.is_(False),
            )
        )
        reset = result.scalar_one_or_none()
        if not reset or SecureTokenGenerator.is_token_expired(reset.expires_at):
            raise ValidationError("Invalid or expired reset token.")
        user = await self.session.get(User, reset.user_id)
        if not user:
            raise NotFoundError("User not found.")
        user.password_hash = PasswordManager.hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        reset.is_used = True
        reset.used_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.info("Password reset completed for user: %s", user.email)

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> None:
        user = await self.session.get(User, user_id)
        if not user:
            raise NotFoundError("User not found.")
        if not PasswordManager.verify_password(current_password, user.password_hash):
            raise ValidationError("Current password is incorrect.")
        is_valid, error = PasswordManager.validate_password_strength(new_password)
        if not is_valid:
            raise ValidationError(error)
        user.password_hash = PasswordManager.hash_password(new_password)
        user.password_changed_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.info("Password changed for user: %s", user.email)

    async def verify_email(self, token: str) -> None:
        token_hash = SecureTokenGenerator.hash_token(token)
        result = await self.session.execute(
            __import__("sqlalchemy").select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.is_used.is_(False),
            )
        )
        verification = result.scalar_one_or_none()
        if not verification or SecureTokenGenerator.is_token_expired(verification.expires_at):
            raise ValidationError("Invalid or expired verification token.")
        user = await self.session.get(User, verification.user_id)
        if not user:
            raise NotFoundError("User not found.")
        user.is_email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        verification.is_used = True
        verification.used_at = datetime.now(timezone.utc)
        await self.session.flush()
        logger.info("Email verified for user: %s", user.email)

    async def create_verification_token(self, user_id: UUID, email: str) -> str:
        raw_token = SecureTokenGenerator.generate_token()
        token_hash = SecureTokenGenerator.hash_token(raw_token)
        verification = EmailVerificationToken(
            user_id=user_id,
            email=email,
            token_hash=token_hash,
            expires_at=SecureTokenGenerator.generate_expires_at(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        )
        self.session.add(verification)
        await self.session.flush()
        return raw_token

    async def _store_refresh_token(self, user_id: UUID, token: str) -> None:
        token_hash = SecureTokenGenerator.hash_token(token)
        refresh = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=SecureTokenGenerator.generate_expires_at(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.session.add(refresh)

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)