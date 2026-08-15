"""Dataset repository for database operations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset, DatasetVersion, UploadedFile, ValidationReport
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def list_datasets(
        self,
        owner_id: UUID | None = None,
        organization_id: UUID | None = None,
        query: str | None = None,
        is_deleted: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Dataset], int]:
        stmt = select(Dataset).where(Dataset.is_deleted.is_(is_deleted))
        if owner_id:
            stmt = stmt.where(Dataset.owner_id == owner_id)
        if organization_id:
            stmt = stmt.where(Dataset.organization_id == organization_id)
        if query:
            stmt = stmt.where(
                Dataset.name.ilike(f"%{query}%")
                | Dataset.description.ilike(f"%{query}%")
            )
        count_stmt = select(func.count(Dataset.id)).where(Dataset.is_deleted.is_(is_deleted))
        if owner_id:
            count_stmt = count_stmt.where(Dataset.owner_id == owner_id)
        if organization_id:
            count_stmt = count_stmt.where(Dataset.organization_id == organization_id)
        if query:
            count_stmt = count_stmt.where(
                Dataset.name.ilike(f"%{query}%")
                | Dataset.description.ilike(f"%{query}%")
            )
        total = (await self.session.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def find_by_checksum(self, checksum: str) -> UploadedFile | None:
        stmt = select(UploadedFile).where(UploadedFile.checksum_sha256 == checksum)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_versions(self, dataset_id: UUID) -> list[DatasetVersion]:
        stmt = (
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id)
            .order_by(DatasetVersion.version_number.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_current_version(self, dataset_id: UUID) -> DatasetVersion | None:
        stmt = (
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id, DatasetVersion.is_current.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_validation_report(self, version_id: UUID) -> ValidationReport | None:
        stmt = select(ValidationReport).where(ValidationReport.version_id == version_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_file_by_version(self, version_id: UUID) -> UploadedFile | None:
        stmt = select(UploadedFile).where(UploadedFile.version_id == version_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()