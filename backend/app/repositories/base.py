"""
Abstract base repository implementing the Repository pattern.

Provides a generic CRUD interface that all domain repositories should
extend. Uses SQLAlchemy async sessions and generic type parameters for
type-safe implementations.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic repository providing common database operations.

    Type parameter ``ModelT`` should be bound to a SQLAlchemy model
    class that inherits from ``Base``.

    Usage:
        class CustomerRepository(BaseRepository[Customer]):
            pass
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialise the repository with a database session.

        Args:
            session: An active SQLAlchemy async session.
        """
        self.session = session

    async def create(self, model: ModelT) -> ModelT:
        """
        Persist a new model instance to the database.

        Args:
            model: The model instance to create.

        Returns:
            The created model instance with generated fields populated.
        """
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def get(self, id: Any) -> ModelT | None:
        """
        Retrieve a model instance by its primary key.

        Args:
            id: The primary key value to look up.

        Returns:
            The model instance if found, otherwise ``None``.
        """
        return await self.session.get(self._model_class, id)

    async def exists(self, id: Any) -> bool:
        """
        Check whether a record with the given primary key exists.

        Args:
            id: The primary key value to check.

        Returns:
            ``True`` if the record exists, ``False`` otherwise.
        """
        result = await self.session.get(self._model_class, id)
        return result is not None

    async def count(self) -> int:
        """
        Return the total number of records for this model.

        Returns:
            The total record count.
        """
        query = select(func.count()).select_from(self._model_class)
        result = await self.session.execute(query)
        return result.scalar_one()

    @property
    def _model_class(self) -> type[ModelT]:
        """Infer the model class from the generic type parameter."""
        return self.__class__.__orig_bases__[0].__args__[0]  # type: ignore[attr-defined]

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelT]:
        """
        Retrieve a paginated list of model instances.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.

        Returns:
            A list of model instances.
        """
        query = select(self._model_class).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())