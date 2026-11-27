"""Breadcrumb trail for the Finder path bar.

Headless: it only computes labels and paths from an absolute path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = ["Crumb", "breadcrumbs"]


@dataclass(frozen=True)
class Crumb:
    """One clickable segment of the path bar."""

    label: str
    path: Path


def breadcrumbs(path: Path) -> list[Crumb]:
    """Return the crumbs from the root to ``path``, inclusive.

    The root crumb is labelled ``/``. Each following crumb is one path component.
    ``path`` must be absolute; ``..`` and ``.`` components are not allowed, so
    the result always matches the path's real components.
    """
    if not path.is_absolute():
        raise ValueError(f"breadcrumbs need an absolute path: {str(path)!r}")
    if any(part in {".", ".."} for part in path.parts):
        raise ValueError(f"path must not contain '.' or '..': {str(path)!r}")

    crumbs = [Crumb(label="/", path=Path(path.anchor))]
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        crumbs.append(Crumb(label=part, path=current))
    return crumbs
