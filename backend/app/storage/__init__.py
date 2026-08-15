"""
Storage abstraction layer for dataset files.

Provides a pluggable StorageProvider interface with a LocalStorageProvider
implementation. Future cloud providers (S3, Azure Blob, GCS) can be added
by implementing the StorageProvider protocol.
"""

from app.storage.base import StorageProvider, StorageError
from app.storage.local import LocalStorageProvider
from app.storage.factory import get_storage_provider

__all__ = ["StorageProvider", "StorageError", "LocalStorageProvider", "get_storage_provider"]