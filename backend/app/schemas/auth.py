"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(..., min_length=8, description="Strong password meeting policy requirements.")
    first_name: str = Field(..., min_length=1, max_length=128, description="Given name.")
    last_name: str = Field(..., min_length=1, max_length=128, description="Family name.")
    organization_name: str | None = Field(None, max_length=256, description="Optional organization name for new organizations.")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address.")
    password: str = Field(..., description="Account password.")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    refresh_token: str = Field(..., description="JWT refresh token.")
    token_type: str = Field("bearer", description="Token type (always 'bearer').")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token.")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token to revoke.")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address.")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token from email.")
    new_password: str = Field(..., min_length=8, description="New password meeting policy.")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password for verification.")
    new_password: str = Field(..., min_length=8, description="New password meeting policy.")


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Email verification token.")


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to resend verification for.")


class UserResponse(BaseModel):
    id: str = Field(..., description="User UUID.")
    email: str = Field(..., description="Email address.")
    first_name: str = Field(..., description="Given name.")
    last_name: str = Field(..., description="Family name.")
    is_email_verified: bool = Field(..., description="Email verification status.")
    is_active: bool = Field(..., description="Account active status.")
    timezone: str = Field("UTC", description="IANA timezone.")
    language: str = Field("en", description="ISO 639-1 language code.")
    created_at: datetime = Field(..., description="Account creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")


class MessageResponse(BaseModel):
    message: str = Field(..., description="Human-readable status message.")