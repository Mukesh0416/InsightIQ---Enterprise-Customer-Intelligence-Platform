"""
General-purpose utility functions for the InsightIQ backend.

Provides pure helper functions that can be used across layers.
"""

from __future__ import annotations

import re


def snake_to_camel(name: str) -> str:
    """
    Convert a ``snake_case`` string to ``camelCase``.

    Args:
        name: The snake_case string to convert.

    Returns:
        The converted camelCase string.

    Example:
        >>> snake_to_camel("user_profile")
        'userProfile'
    """
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def build_api_url(host: str, port: int, prefix: str, path: str) -> str:
    """
    Construct a full API URL from its components.

    Args:
        host: The hostname or IP address.
        port: The port number.
        prefix: The API prefix (e.g. ``/api/v1``).
        path: The endpoint path (e.g. ``/health``).

    Returns:
        A fully qualified URL string.
    """
    base = f"http://{host}:{port}"
    prefix_clean = prefix.strip("/")
    path_clean = path.strip("/")
    return f"{base}/{prefix_clean}/{path_clean}"