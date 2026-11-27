"""Unit tests for applications/finder (docs/specifications/finder-core.md)."""

from __future__ import annotations

import os
import time
from collections.abc import Iterable
from pathlib import Path

import pytest

from tree_finder import (
    Entry,
    FinderError,
    NavigationHistory,
    SortKey,
    breadcrumbs,
    list_directory,
    sort_entries,
)


def _names(entries: Iterable[Entry]) -> list[str]:
    return [entry.name for entry in entries]


@pytest.fixture
def sample(tmp_path: Path) -> Path:
    (tmp_path / "Zeta").mkdir()
    (tmp_path / "alpha").mkdir()
    (tmp_path / "big.bin").write_bytes(b"x" * 500)
    (tmp_path / "Beta.txt").write_bytes(b"x" * 10)
    (tmp_path / ".secret").write_text("hidden", encoding="utf-8")
    now = time.time()
    os.utime(tmp_path / "Beta.txt", (now - 100, now - 100))
    os.utime(tmp_path / "big.bin", (now - 50, now - 50))
    return tmp_path


# --- list_directory ---------------------------------------------------------


def test_hidden_entries_are_omitted_by_default(sample: Path) -> None:
    assert ".secret" not in _names(list_directory(sample))


def test_hidden_entries_are_included_on_request(sample: Path) -> None:
    entries = list_directory(sample, include_hidden=True)
    hidden = [e for e in entries if e.name == ".secret"]
    assert len(hidden) == 1
    assert hidden[0].is_hidden is True


def test_folders_come_before_files_when_sorted_by_name(sample: Path) -> None:
    names = _names(list_directory(sample))
    assert names == ["alpha", "Zeta", "Beta.txt", "big.bin"]


def test_name_sort_is_case_insensitive(sample: Path) -> None:
    names = _names(list_directory(sample, sort_by=SortKey.NAME))
    assert names.index("alpha") < names.index("Zeta")


def test_sort_by_size_puts_largest_file_last(sample: Path) -> None:
    files = [e for e in list_directory(sample, sort_by=SortKey.SIZE) if not e.is_dir]
    assert _names(files) == ["Beta.txt", "big.bin"]


def test_sort_by_modified_puts_newest_last(sample: Path) -> None:
    files = [
        e for e in list_directory(sample, sort_by=SortKey.MODIFIED) if not e.is_dir
    ]
    assert _names(files) == ["Beta.txt", "big.bin"]


def test_reverse_keeps_folders_first(sample: Path) -> None:
    names = _names(list_directory(sample, reverse=True))
    assert names == ["Zeta", "alpha", "big.bin", "Beta.txt"]


def test_entry_fields_describe_the_file(sample: Path) -> None:
    by_name = {e.name: e for e in list_directory(sample)}
    beta = by_name["Beta.txt"]
    assert beta.path == sample / "Beta.txt"
    assert beta.is_dir is False
    assert beta.size == 10
    assert by_name["alpha"].is_dir is True
    assert by_name["alpha"].size == 0


def test_symlink_to_directory_is_not_treated_as_directory(tmp_path: Path) -> None:
    target = tmp_path / "real"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    by_name = {e.name: e for e in list_directory(tmp_path)}
    assert by_name["link"].is_symlink is True
    assert by_name["link"].is_dir is False


def test_relative_path_is_rejected() -> None:
    with pytest.raises(FinderError, match="must be absolute"):
        list_directory(Path("relative/dir"))


def test_nul_byte_in_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FinderError, match="NUL"):
        list_directory(Path(str(tmp_path) + "\x00x"))


def test_missing_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FinderError, match="not a directory"):
        list_directory(tmp_path / "missing")


def test_file_path_is_rejected(sample: Path) -> None:
    with pytest.raises(FinderError, match="not a directory"):
        list_directory(sample / "Beta.txt")


def test_scan_errors_are_reported_as_finder_errors(tmp_path: Path) -> None:
    def denied(_path: Path) -> Iterable[os.DirEntry[str]]:
        raise PermissionError(13, "Permission denied")

    with pytest.raises(FinderError, match="Permission denied") as info:
        list_directory(tmp_path, scan=denied)
    assert isinstance(info.value.__cause__, PermissionError)


def test_listing_does_not_modify_the_directory(sample: Path) -> None:
    before = sorted(p.name for p in sample.iterdir())
    list_directory(sample, include_hidden=True)
    assert sorted(p.name for p in sample.iterdir()) == before


# --- sort_entries -----------------------------------------------------------


def _entry(
    name: str, *, is_dir: bool = False, size: int = 0, mtime: float = 0
) -> Entry:
    return Entry(
        name=name,
        path=Path("/x") / name,
        is_dir=is_dir,
        is_symlink=False,
        is_hidden=name.startswith("."),
        size=size,
        modified=mtime,
    )


def test_sort_entries_breaks_ties_by_name() -> None:
    entries = [_entry("b", size=1), _entry("a", size=1)]
    assert _names(sort_entries(entries, sort_by=SortKey.SIZE)) == ["a", "b"]


def test_sort_entries_handles_empty_input() -> None:
    assert sort_entries([]) == []


# --- NavigationHistory ------------------------------------------------------


def test_history_starts_at_given_location() -> None:
    history = NavigationHistory(Path("/home"))
    assert history.current == Path("/home")
    assert history.can_go_back is False
    assert history.can_go_forward is False


def test_history_back_and_forward() -> None:
    history = NavigationHistory(Path("/a"))
    history.navigate(Path("/a/b"))
    history.navigate(Path("/a/b/c"))
    assert history.back() == Path("/a/b")
    assert history.back() == Path("/a")
    assert history.can_go_back is False
    assert history.forward() == Path("/a/b")
    assert history.current == Path("/a/b")


def test_navigating_discards_forward_history() -> None:
    history = NavigationHistory(Path("/a"))
    history.navigate(Path("/b"))
    history.back()
    history.navigate(Path("/c"))
    assert history.can_go_forward is False
    assert history.back() == Path("/a")


def test_navigating_to_current_location_adds_no_entry() -> None:
    history = NavigationHistory(Path("/a"))
    history.navigate(Path("/a"))
    assert history.can_go_back is False


def test_back_at_start_raises() -> None:
    with pytest.raises(ValueError, match="no earlier"):
        NavigationHistory(Path("/a")).back()


def test_forward_at_end_raises() -> None:
    with pytest.raises(ValueError, match="no later"):
        NavigationHistory(Path("/a")).forward()


def test_history_rejects_relative_paths() -> None:
    with pytest.raises(ValueError):
        NavigationHistory(Path("rel"))
    history = NavigationHistory(Path("/a"))
    with pytest.raises(ValueError):
        history.navigate(Path("rel"))


# --- breadcrumbs ------------------------------------------------------------


def test_breadcrumbs_for_root() -> None:
    crumbs = breadcrumbs(Path("/"))
    assert [(c.label, c.path) for c in crumbs] == [("/", Path("/"))]


def test_breadcrumbs_run_from_root_to_path() -> None:
    crumbs = breadcrumbs(Path("/home/riki/Documents"))
    assert [c.label for c in crumbs] == ["/", "home", "riki", "Documents"]
    assert crumbs[2].path == Path("/home/riki")
    assert crumbs[-1].path == Path("/home/riki/Documents")


def test_breadcrumbs_reject_relative_paths() -> None:
    with pytest.raises(ValueError, match="absolute"):
        breadcrumbs(Path("home/riki"))


def test_breadcrumbs_reject_parent_components() -> None:
    with pytest.raises(ValueError, match="must not contain"):
        breadcrumbs(Path("/home/../etc"))


def test_breadcrumbs_collapse_current_directory_components() -> None:
    # pathlib drops "." on its own, so the result never contains it.
    assert [c.label for c in breadcrumbs(Path("/home/./riki"))] == [
        "/",
        "home",
        "riki",
    ]
