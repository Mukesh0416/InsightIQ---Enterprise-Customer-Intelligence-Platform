"""
Column header validation for dataset uploads.

Detects missing, duplicate, blank, or malformed column headers.
"""

from __future__ import annotations

import re

from app.exceptions import ValidationError

RESERVED_KEYWORDS = {
    "select", "insert", "update", "delete", "drop", "alter",
    "create", "grant", "revoke", "order", "group", "where",
    "from", "table", "index", "primary", "foreign",
}

INVALID_CHARS = re.compile(r"[^\w\s\-\.\(\)\[\]/\:%]")
WHITESPACE_ONLY = re.compile(r"^\s*$")


class ColumnValidator:
    """Validates column headers for datasets."""

    VALID_HEADER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_\s\.\-\(\)]*$")

    @classmethod
    def validate_headers(cls, headers: list[str]) -> list[str]:
        if not headers:
            raise ValidationError("Dataset has no columns.")

        issues: list[str] = []
        seen: dict[str, int] = {}
        cleaned: list[str] = []

        for idx, header in enumerate(headers):
            header_str = str(header).strip()

            # Blank column name
            if not header_str or WHITESPACE_ONLY.match(header_str):
                issues.append(f"Column {idx + 1} has a blank name.")

            # Invalid characters
            if INVALID_CHARS.search(header_str):
                issues.append(f"Column '{header_str}' contains invalid characters.")

            # Reserved keywords
            if header_str.lower() in RESERVED_KEYWORDS:
                issues.append(f"Column '{header_str}' is a reserved keyword.")

            # Duplicates
            lower = header_str.lower()
            if lower in seen:
                issues.append(f"Duplicate column name: '{header_str}' (also at position {seen[lower] + 1}).")
            else:
                seen[lower] = idx

            cleaned.append(header_str)

        if issues:
            raise ValidationError("Column validation failed: " + "; ".join(issues))

        return cleaned