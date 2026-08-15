"""
SQLAlchemy ORM models for the InsightIQ domain.

Import all models here to ensure they are registered with SQLAlchemy metadata.
"""

from app.models.base import BaseModel
from app.models.user import User
from app.models.role import Role, Permission, RolePermission
from app.models.organization import Organization, OrganizationMember
from app.models.invitation import Invitation
from app.models.token import RefreshToken, PasswordResetToken, EmailVerificationToken
from app.models.audit_log import AuditLog
from app.models.dataset import (
    Dataset,
    DatasetVersion,
    UploadedFile,
    DatasetMetadata,
    ProcessingJob,
    ValidationReport,
)
from app.models.ai import (
    MLModel,
    MLExperiment,
    TrainingRun,
    Prediction,
    PredictionBatch,
    ModelMetrics,
    DriftReport,
    FeatureMetadata,
    ModelArtifact,
)
from app.models.services import (
    Report,
    ExportJob,
    Notification,
    NotificationPreference,
    BackgroundJob,
    ScheduledTask,
    AuditEvent,
    ActivityLog,
    DashboardCache,
)

__all__ = [
    "BaseModel",
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "Organization",
    "OrganizationMember",
    "Invitation",
    "RefreshToken",
    "PasswordResetToken",
    "EmailVerificationToken",
    "AuditLog",
    "Dataset",
    "DatasetVersion",
    "UploadedFile",
    "DatasetMetadata",
    "ProcessingJob",
    "ValidationReport",
    "MLModel",
    "MLExperiment",
    "TrainingRun",
    "Prediction",
    "PredictionBatch",
    "ModelMetrics",
    "DriftReport",
    "FeatureMetadata",
    "ModelArtifact",
    "Report",
    "ExportJob",
    "Notification",
    "NotificationPreference",
    "BackgroundJob",
    "ScheduledTask",
    "AuditEvent",
    "ActivityLog",
    "DashboardCache",
]