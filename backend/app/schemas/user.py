"""Pydantic schemas for user management endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address.")
    password: str = Field(..., min_length=8, description="Password meeting policy.")
    first_name: str = Field(..., min_length=1, max_length=128, description="Given name.")
    last_name: str = Field(..., min_length=1, max_length=128, description="Family name.")
    phone: str | None = Field(None, max_length=32, description="Phone number (E.164).")
    timezone: str = Field("UTC", max_length=64, description="IANA timezone.")
    language: str = Field("en", max_length=10, description="ISO 639-1 language code.")
    role_id: str | None = Field(None, description="UUID of the role to assign.")
    organization_id: str | None = Field(None, description="UUID of the organization.")


class UserUpdateRequest(BaseModel):
    first_name: str | None = Field(None, max_length=128, description="Given name.")
    last_name: str | None = Field(None, max_length=128, description="Family name.")
    phone: str | None = Field(None, max_length=32, description="Phone number.")
    timezone: str | None = Field(None, max_length=64, description="IANA timezone.")
    language: str | None = Field(None, max_length=10, description="ISO 639-1 language code.")
    profile_image_url: str | None = Field(None, max_length=1024, description="Avatar URL.")


class UserReadResponse(BaseModel):
    id: UUID = Field(..., description="User UUID.")
    email: str = Field(..., description="Email address.")
    first_name: str = Field(..., description="Given name.")
    last_name: str = Field(..., description="Family name.")
    phone: str | None = Field(None, description="Phone number.")
    profile_image_url: str | None = Field(None, description="Avatar URL.")
    timezone: str = Field(..., description="IANA timezone.")
    language: str = Field(..., description="ISO 639-1 language code.")
    is_email_verified: bool = Field(..., description="Email verification status.")
    is_active: bool = Field(..., description="Account active status.")
    is_locked: bool = Field(..., description="Account lockout status.")
    last_login_at: datetime | None = Field(None, description="Last login timestamp.")
    organization_id: str | None = Field(None, description="Organization UUID.")
    role_id: str | None = Field(None, description="Role UUID.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")


class UserListResponse(BaseModel):
    items: list[UserReadResponse] = Field(..., description="List of users.")
    total: int = Field(..., description="Total count.")
    page: int = Field(..., description="Current page.")
    page_size: int = Field(..., description="Items per page.")
    total_pages: int = Field(..., description="Total pages.")