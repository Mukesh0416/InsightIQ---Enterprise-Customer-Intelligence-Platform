"""Pydantic schemas for organization management endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256, description="Organization display name.")
    description: str | None = Field(None, description="Optional description.")


class OrganizationUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=256, description="Display name.")
    description: str | None = Field(None, description="Description.")


class OrganizationReadResponse(BaseModel):
    id: UUID = Field(..., description="Organization UUID.")
    name: str = Field(..., description="Display name.")
    slug: str = Field(..., description="URL-safe slug.")
    description: str | None = Field(None, description="Description.")
    owner_id: UUID | None = Field(None, description="Owner user UUID.")
    is_active: bool = Field(..., description="Active status.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")


class OrganizationListResponse(BaseModel):
    items: list[OrganizationReadResponse] = Field(..., description="List of organizations.")
    total: int = Field(..., description="Total count.")
    page: int = Field(..., description="Current page.")
    page_size: int = Field(..., description="Items per page.")
    total_pages: int = Field(..., description="Total pages.")


class InviteMemberRequest(BaseModel):
    email: EmailStr = Field(..., description="Email of the person to invite.")
    role_id: str | None = Field(None, description="UUID of the role to assign.")
    message: str | None = Field(None, max_length=1000, description="Personal message.")


class MemberResponse(BaseModel):
    id: UUID = Field(..., description="Member record UUID.")
    user_id: UUID = Field(..., description="User UUID.")
    email: str = Field(..., description="User email.")
    first_name: str = Field(..., description="User given name.")
    last_name: str = Field(..., description="User family name.")
    role: str = Field(..., description="Member role in org.")
    joined_at: datetime = Field(..., description="Join timestamp.")


class AcceptInvitationRequest(BaseModel):
    token: str = Field(..., description="Invitation token from email.")
    first_name: str = Field(..., min_length=1, max_length=128, description="Given name.")
    last_name: str = Field(..., min_length=1, max_length=128, description="Family name.")
    password: str = Field(..., min_length=8, description="Password meeting policy.")