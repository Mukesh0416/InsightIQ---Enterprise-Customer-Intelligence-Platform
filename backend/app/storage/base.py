"""
Storage provider interface and error types.

Defines the abstract StorageProvider protocol that all storage backends
must implement. Future cloud providers (S3, Azure Blob, GCS) can plug in
by implementing this protocol.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageError(Exception):
    """Raised when a storage operation fails."""

    def __init__(
        self,
        message: str = "Storage operation failed",
        status_code: int = 500,
        detail: object | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class FileStorageResult:
    """Result of a storage save operation."""

    def __init__(
        self,
        stored_filename: str,
        storage_path: str,
        storage_provider: str,
    ) -> None:
        self.stored_filename = stored_filename
        self.storage_path = storage_path
        self.storage_provider = storage_provider


class StorageProvider(ABC):
    """Abstract interface for file storage providers."""

    @abstractmethod
    async def save(
        self,
        data: bytes,
        original_filename: str,
        unique_id: str,
    ) -> FileStorageResult:
        """Persist file data and return storage metadata."""

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Read and return the file bytes from storage."""

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Delete the file from storage."""

    @abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """Check whether a file exists in storage."""