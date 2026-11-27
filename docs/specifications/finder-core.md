# Specification: TREE Finder core

- **Component:** `applications/finder` (headless core, package `tree_finder`)
- **Status:** Draft, first increment of Sprint 004
- **Language:** Python 3.12 (standard library only)

## Purpose

TREE Finder is the file manager (CLAUDE.md section 9). This first increment
implements its UI-independent logic: reading a directory, sorting it, moving
through navigation history and building the path bar. The GTK4 window is a later
increment that uses this module.

This component is an application, so it may depend on framework components. It
must not import services or the GNOME Shell (CLAUDE.md section 4).

## Scope

In scope:

- Read-only directory listing with hidden-file filtering.
- Sorting by name, size or modification time, folders first.
- Back and forward navigation history.
- Breadcrumb trail for a path.

Out of scope (later increments):

- File copy, move, rename, delete and Trash handling. These change the
  filesystem and need confirmation and progress reporting first.
- GIO/GVfs backends for network and external locations. The core uses
  `os.scandir`, so it only lists local paths for now.
- Previews, search, tabs, windows, archive integration and the GTK UI.

## Interfaces

### `list_directory(path, *, include_hidden=False, sort_by=SortKey.NAME, reverse=False, scan=...) -> list[Entry]`

- `path` must be absolute, contain no NUL byte, and be an existing directory.
  Otherwise `FinderError` is raised.
- Entries are classified without following symbolic links. A link to a
  directory is reported with `is_symlink=True` and `is_dir=False`, and the
  listing never enters it.
- `size` is zero for directories. `modified` is the modification time in seconds.
- An entry is hidden when its name starts with `.`.
- An unreadable directory raises `FinderError` chained to the `OSError`.
- `scan` is injectable so tests can simulate failures. It must raise `OSError`
  for unreadable directories.
- The function never writes to the filesystem.

### `sort_entries(entries, *, sort_by=SortKey.NAME, reverse=False) -> list[Entry]`

- Folders always come before files. `reverse` reverses order inside each group.
- Name order is case-insensitive, with the exact name as a tie-breaker.
- Size and modification order break ties by name.

### `NavigationHistory(start)`

- Linear history. Navigating to a new location discards the forward history.
- Navigating to the current location adds nothing.
- `back()` and `forward()` raise `ValueError` at the ends of the history.
- All paths must be absolute.

### `breadcrumbs(path) -> list[Crumb]`

- Returns one crumb per component, starting with the root labelled `/`.
- `path` must be absolute and must not contain `.` or `..` components.

## Security

- Listing is read-only and runs as the invoking user. The application never
  runs as root (CLAUDE.md section 11).
- Symbolic links are not followed, so the listing cannot be steered outside the
  directory the user opened by a link.
- Paths are validated before use. Relative paths and NUL bytes are rejected.

## Tests

Automated tests in `tests/unit/test_finder_core.py` cover: hidden-file handling,
folders-first ordering, name, size and modification sorting, reverse order,
entry fields, symbolic links, invalid paths, scan failures, read-only behavior,
history navigation and breadcrumbs.

## Limitations

- Local filesystem only (`os.scandir`). Network and external volumes are not
  supported yet.
- The listing reads the whole directory into memory before sorting. This is
  fine for ordinary folders and must be revisited for very large ones.
- Not yet tested on the Ubuntu 24.04 VM. The core uses only the standard library,
  so the VM run is an integration check, not a new dependency check.
