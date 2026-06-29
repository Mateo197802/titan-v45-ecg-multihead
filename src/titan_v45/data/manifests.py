from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath


class LeakageError(RuntimeError):
    """Raised when frozen dataset partitions share record identifiers."""


def sanitize_record_path(path: str) -> str:
    normalized = str(path).replace("\\", "/")
    parts = PurePosixPath(normalized).parts
    marker_index = next(
        (index for index, part in enumerate(parts) if part.lower() == "data"),
        None,
    )
    if marker_index is None or marker_index + 1 >= len(parts):
        raise ValueError(f"path has no DATA-relative component: {path}")
    return "/".join(parts[marker_index + 1 :])


def validate_no_overlap(train_ids: Iterable[str], evaluation_ids: Iterable[str]) -> None:
    overlap = sorted(set(train_ids) & set(evaluation_ids))
    if overlap:
        preview = ", ".join(overlap[:10])
        raise LeakageError(f"dataset partitions overlap: {preview}")
