"""Local filesystem storage provider implementation."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiofiles

from app.config import settings
from app.storage.base import FileStorageResult, StorageError, StorageProvider


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider.

    Files are stored under ``<STORAGE_ROOT>/<org_id>/<unique_id><ext>``.
    Uses aiofiles for non-blocking file I/O.
    """

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or Path(getattr(settings, "STORAGE_ROOT", "storage"))
        self.root_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, data: bytes, original_filename: str, unique_id: str) -> FileStorageResult:
        ext = Path(original_filename).suffix.lower()
        safe_ext = "".join(c for c in ext if c.isalnum() or c == ".")
        stored_name = f"{unique_id}{safe_ext}"
        org_dir = self.root_dir / str(uuid.uuid4())[:8]
        org_dir.mkdir(parents=True, exist_ok=True)
        file_path = org_dir / stored_name
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)
        except OSError as exc:
            raise StorageError(f"Failed to write file: {exc}", status_code=500) from exc
        return FileStorageResult(
            stored_filename=stored_name,
            storage_path=str(file_path.resolve()),
            storage_provider="local",
        )

    async def read(self, storage_path: str) -> bytes:
        try:
            async with aiofiles.open(storage_path, "rb") as f:
                return await f.read()
        except FileNotFoundError as exc:
            raise StorageError("File not found", status_code=404) from exc
        except OSError as exc:
            raise StorageError(f"Failed to read file: {exc}", status_code=500) from exc

    async def delete(self, storage_path: str) -> None:
        try:
            os.remove(storage_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise StorageError(f"Failed to delete file: {exc}", status_code=500) from exc

    async def exists(self, storage_path: str) -> bool:
        return os.path.exists(storage_path)