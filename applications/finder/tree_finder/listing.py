"""Read-only directory listing and sorting for TREE Finder.

See docs/specifications/finder-core.md. This module is headless: it has no GTK
or GIO dependency and never modifies the filesystem.
"""

from __future__ import annotations

import enum
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "Entry",
    "FinderError",
    "ScanFunc",
    "SortKey",
    "list_directory",
    "sort_entries",
]


class FinderError(Exception):
    """Raised for every expected listing failure."""


class SortKey(enum.Enum):
    """Columns the user can sort by."""

    NAME = "name"
    SIZE = "size"
    MODIFIED = "modified"


@dataclass(frozen=True)
class Entry:
    """One item in a directory listing."""

    name: str
    path: Path
    is_dir: bool
    is_symlink: bool
    is_hidden: bool
    size: int
    modified: float


# A scanner returns the raw entries of a directory. The default uses os.scandir;
# tests inject their own. It must raise OSError for unreadable directories.
ScanFunc = Callable[[Path], Iterable[os.DirEntry[str]]]


def _default_scan(path: Path) -> Iterable[os.DirEntry[str]]:
    with os.scandir(path) as iterator:
        return list(iterator)


def _to_entry(raw: os.DirEntry[str], directory: Path) -> Entry:
    # Do not follow symlinks when classifying: a link to a directory is shown as
    # a link, and listing never walks into it.
    is_symlink = raw.is_symlink()
    is_dir = raw.is_dir(follow_symlinks=False)
    stat = raw.stat(follow_symlinks=False)
    return Entry(
        name=raw.name,
        path=directory / raw.name,
        is_dir=is_dir,
        is_symlink=is_symlink,
        is_hidden=raw.name.startswith("."),
        size=0 if is_dir else stat.st_size,
        modified=stat.st_mtime,
    )


def list_directory(
    path: Path,
    *,
    include_hidden: bool = False,
    sort_by: SortKey = SortKey.NAME,
    reverse: bool = False,
    scan: ScanFunc = _default_scan,
) -> list[Entry]:
    """Return the entries of ``path``, sorted with folders first.

    ``path`` must be an absolute path. Hidden entries (names starting with ``.``)
    are omitted unless ``include_hidden`` is true. Raises ``FinderError`` if the
    path is not an absolute directory or cannot be read.
    """
    if not path.is_absolute():
        raise FinderError(f"path must be absolute: {str(path)!r}")
    if "\x00" in str(path):
        raise FinderError("path contains a NUL byte")
    if not path.is_dir():
        raise FinderError(f"not a directory: {str(path)!r}")

    try:
        raw_entries = scan(path)
        entries = [_to_entry(raw, path) for raw in raw_entries]
    except OSError as exc:
        raise FinderError(f"cannot read {str(path)!r}: {exc.strerror}") from exc

    if not include_hidden:
        entries = [entry for entry in entries if not entry.is_hidden]
    return sort_entries(entries, sort_by=sort_by, reverse=reverse)


def sort_entries(
    entries: Iterable[Entry],
    *,
    sort_by: SortKey = SortKey.NAME,
    reverse: bool = False,
) -> list[Entry]:
    """Sort entries by ``sort_by``, keeping folders before files.

    Name sorting is case-insensitive and falls back to the exact name so the
    order is deterministic. ``reverse`` reverses the order inside each group.
    """
    items = list(entries)

    def key(entry: Entry) -> tuple[object, ...]:
        if sort_by is SortKey.NAME:
            return (entry.name.casefold(), entry.name)
        if sort_by is SortKey.SIZE:
            return (entry.size, entry.name.casefold(), entry.name)
        return (entry.modified, entry.name.casefold(), entry.name)

    folders = sorted((e for e in items if e.is_dir), key=key, reverse=reverse)
    files = sorted((e for e in items if not e.is_dir), key=key, reverse=reverse)
    return folders + files
