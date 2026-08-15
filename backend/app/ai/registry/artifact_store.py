"""Artifact storage for ML models."""

from __future__ import annotations

import hashlib
import io
import os
import pickle
from pathlib import Path
from typing import Any

ARTIFACT_ROOT = Path("artifacts/models")


def _ensure_dir() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)


def save_artifact(
    model: Any,
    model_id: str,
    artifact_type: str = "model",
    version: int = 1,
) -> dict[str, Any]:
    """Serialize and save a model artifact to disk."""
    _ensure_dir()
    filename = f"{model_id}_v{version}_{artifact_type}.pkl"
    path = ARTIFACT_ROOT / filename

    # Serialize model
    buffer = io.BytesIO()
    pickle.dump(model, buffer)
    data = buffer.getvalue()

    # Write to disk
    path.write_bytes(data)

    # Compute checksum
    checksum = hashlib.sha256(data).hexdigest()

    return {
        "artifact_path": str(path.resolve()),
        "file_size_bytes": len(data),
        "checksum_sha256": checksum,
    }


def load_artifact(artifact_path: str) -> Any:
    """Load a serialized model artifact from disk."""
    path = Path(artifact_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    with open(path, "rb") as f:
        return pickle.load(f)


def delete_artifact(artifact_path: str) -> None:
    """Delete a model artifact from disk."""
    try:
        os.remove(artifact_path)
    except FileNotFoundError:
        pass