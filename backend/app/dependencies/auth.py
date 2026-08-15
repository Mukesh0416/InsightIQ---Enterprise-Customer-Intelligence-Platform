"""Authentication and authorization dependencies for FastAPI routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db_session
from app.models.user import User
from app.repositories.user import UserRepository
from app.security.jwt import JWTManager

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if credentials is None:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    else:
        token = credentials.credentials
    try:
        subject = JWTManager.get_subject(token)
        token_type = JWTManager.get_token_type(token)
        if token_type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    user_repo = UserRepository(session)
    user = await user_repo.get(UUID(subject))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User | None:
    if credentials is None:
        return None
    try:
        subject = JWTManager.get_subject(credentials.credentials)
    except JWTError:
        return None
    user_repo = UserRepository(session)
    return await user_repo.get(UUID(subject))


def require_permission(permission_codename: str):
    async def permission_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No role assigned.")
        has_perm = any(p.codename == permission_codename for p in current_user.role.permissions)
        if not has_perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission_codename}")
        return current_user
    return permission_dependency