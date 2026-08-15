"""API v1 router – versioned endpoint collection."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.eda import router as eda_router
from app.api.v1.business import router as business_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(organizations_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(eda_router)
api_v1_router.include_router(business_router)

__all__ = ["api_v1_router"]