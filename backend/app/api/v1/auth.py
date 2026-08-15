"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db_session
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest, ForgotPasswordRequest, LoginRequest, LogoutRequest,
    MessageResponse, RefreshTokenRequest, RegisterRequest, ResendVerificationRequest,
    ResetPasswordRequest, TokenResponse, UserResponse, VerifyEmailRequest,
)
from app.services.auth import AuthService

router = APIRouter(tags=["Authentication"])


@router.post("/auth/register", response_model=MessageResponse, status_code=201)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    await service.register(body.email, body.password, body.first_name, body.last_name)
    return MessageResponse(message="Registration successful. Please verify your email.")


@router.post("/auth/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    ip = request.client.host if request.client else None
    access_token, refresh_token, _ = await service.login(body.email, body.password, ip)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/auth/logout", response_model=MessageResponse)
async def logout(body: LogoutRequest, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    await service.logout(body.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(body: RefreshTokenRequest, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    access_token, refresh_token = await service.refresh(body.refresh_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/auth/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    await service.forgot_password(body.email)
    return MessageResponse(message="If the email exists, a reset link has been sent.")


@router.post("/auth/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    await service.reset_password(body.token, body.new_password)
    return MessageResponse(message="Password reset successfully.")


@router.post("/auth/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = AuthService(session)
    await service.change_password(current_user.id, body.current_password, body.new_password)
    return MessageResponse(message="Password changed successfully.")


@router.post("/auth/verify-email", response_model=MessageResponse)
async def verify_email(body: VerifyEmailRequest, session: AsyncSession = Depends(get_db_session)):
    service = AuthService(session)
    await service.verify_email(body.token)
    return MessageResponse(message="Email verified successfully.")


@router.post("/auth/resend-verification", response_model=MessageResponse)
async def resend_verification(body: ResendVerificationRequest, session: AsyncSession = Depends(get_db_session)):
    from app.repositories.user import UserRepository
    repo = UserRepository(session)
    user = await repo.find_by_email(body.email)
    if user and not user.is_email_verified:
        service = AuthService(session)
        await service.create_verification_token(user.id, user.email)
    return MessageResponse(message="If the email exists, a verification link has been sent.")


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_email_verified=current_user.is_email_verified,
        is_active=current_user.is_active,
        timezone=current_user.timezone,
        language=current_user.language,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )