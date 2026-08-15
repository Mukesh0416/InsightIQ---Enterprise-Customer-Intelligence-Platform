"""Storage provider factory for selecting the active provider."""

from __future__ import annotations

from app.config import settings
from app.storage.base import StorageProvider
from app.storage.local import LocalStorageProvider

_provider: StorageProvider | None = None


def get_storage_provider() -> StorageProvider:
    """Return the configured storage provider singleton."""
    global _provider
    if _provider is None:
        provider_name = getattr(settings, "STORAGE_PROVIDER", "local")
        if provider_name == "local":
            _provider = LocalStorageProvider()
        else:
            # Future: S3Provider(), AzureBlobProvider(), GCSProvider()
            raise ValueError(f"Unsupported storage provider: {provider_name}")
    return _provider