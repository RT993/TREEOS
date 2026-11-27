"""Back and forward navigation history for a Finder window.

Headless: it stores paths and never touches the filesystem.
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["NavigationHistory"]


class NavigationHistory:
    """Linear back/forward history, like a browser or Finder window.

    Navigating to a new location discards the forward history. Navigating to
    the current location is a no-op, so a refresh does not add an entry.
    """

    def __init__(self, start: Path) -> None:
        if not start.is_absolute():
            raise ValueError(f"history paths must be absolute: {str(start)!r}")
        self._entries: list[Path] = [start]
        self._index = 0

    @property
    def current(self) -> Path:
        return self._entries[self._index]

    @property
    def can_go_back(self) -> bool:
        return self._index > 0

    @property
    def can_go_forward(self) -> bool:
        return self._index < len(self._entries) - 1

    def navigate(self, path: Path) -> None:
        """Make ``path`` the current location, recording it in the history."""
        if not path.is_absolute():
            raise ValueError(f"history paths must be absolute: {str(path)!r}")
        if path == self.current:
            return
        del self._entries[self._index + 1 :]
        self._entries.append(path)
        self._index += 1

    def back(self) -> Path:
        """Move back one entry and return the new current location."""
        if not self.can_go_back:
            raise ValueError("no earlier location in history")
        self._index -= 1
        return self.current

    def forward(self) -> Path:
        """Move forward one entry and return the new current location."""
        if not self.can_go_forward:
            raise ValueError("no later location in history")
        self._index += 1
        return self.current
