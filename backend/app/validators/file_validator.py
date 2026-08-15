"""
File validation for dataset uploads.

Validates file extension, MIME type, size limits, and checksum deduplication.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.config import settings
from app.exceptions import ValidationError

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
SUPPORTED_MIME_TYPES = {
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",
}


class FileValidator:
    """Validates uploaded dataset files."""

    def __init__(self) -> None:
        self.max_size = getattr(settings, "DATASET_MAX_FILE_SIZE_MB", 100) * 1024 * 1024
        self.max_rows = getattr(settings, "DATASET_MAX_ROWS", 1_000_000)
        self.max_columns = getattr(settings, "DATASET_MAX_COLUMNS", 500)

    def validate_extension(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"Unsupported file extension '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        return ext

    def validate_mime_type(self, mime_type: str | None) -> None:
        if mime_type and mime_type not in SUPPORTED_MIME_TYPES:
            raise ValidationError(f"Unsupported MIME type: {mime_type}")

    def validate_size(self, size: int) -> None:
        if size <= 0:
            raise ValidationError("Cannot upload an empty file.")
        if size > self.max_size:
            raise ValidationError(
                f"File exceeds maximum allowed size of {self.max_size // (1024*1024)} MB."
            )

    def validate_filename(self, filename: str) -> str:
        cleaned = Path(filename).name  # Strip any path components
        if not cleaned or cleaned in {".", ".."}:
            raise ValidationError("Invalid filename.")
        if "\\" in filename or "/" in filename:
            raise ValidationError("Path traversal attempts are not allowed.")
        return cleaned

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()