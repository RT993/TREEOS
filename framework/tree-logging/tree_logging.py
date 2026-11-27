"""Consistent logging for TREE OS components with secret redaction.

See docs/specifications/tree-logging.md for the contract this module implements.
This module uses only the standard library and must not import application or
service code (CLAUDE.md section 4).
"""

from __future__ import annotations

import logging
import re
from typing import Final, TextIO

__all__ = [
    "LOGGER_ROOT",
    "REDACTED",
    "SecretRedactionFilter",
    "configure",
    "get_logger",
    "redact_text",
]

LOGGER_ROOT: Final[str] = "treeos"
REDACTED: Final[str] = "<redacted>"

_COMPONENT_RE: Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9-]*")
_LEVELS: Final[frozenset[str]] = frozenset(
    {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
)

# Matches "password=value", "token: value", "api_key = value" and similar, where
# the value runs to the next whitespace or quote. The key name is kept so the
# log line still says what was removed.
_SECRET_TEXT_RE: Final[re.Pattern[str]] = re.compile(
    r"(?i)\b(password|passwd|passphrase|secret|token|api[_-]?key|private[_-]?key)"
    r"(\s*[=:]\s*)"
    r"(\"[^\"]*\"|'[^']*'|[^\s,;&]+)"
)

# Attribute names (for `extra=` fields) that are always redacted.
_SECRET_KEY_RE: Final[re.Pattern[str]] = re.compile(
    r"(?i)(password|passwd|passphrase|secret|token|api[_-]?key|private[_-]?key)"
)

# Attributes every LogRecord has. Anything else came from `extra=`.
_STANDARD_ATTRS: Final[frozenset[str]] = frozenset(
    vars(logging.LogRecord("", 0, "", 0, "", None, None)).keys()
) | {"message", "asctime", "taskName"}

_HANDLER_MARK: Final[str] = "_treeos_handler"


def _mask_match(match: re.Match[str]) -> str:
    key, separator, value = match.group(1), match.group(2), match.group(3)
    if value[0] in "\"'":
        quote = value[0]
        return f"{key}{separator}{quote}{REDACTED}{quote}"
    return f"{key}{separator}{REDACTED}"


def redact_text(text: str) -> str:
    """Return ``text`` with the values of secret-looking ``key=value`` pairs masked."""
    return _SECRET_TEXT_RE.sub(_mask_match, text)


def get_logger(component: str) -> logging.Logger:
    """Return the logger for a TREE OS component, named ``treeos.<component>``.

    ``component`` must match ``[a-z][a-z0-9-]*``. Anything else raises
    ``ValueError`` so that logger names stay predictable.
    """
    if not _COMPONENT_RE.fullmatch(component):
        raise ValueError(f"invalid component name {component!r}")
    return logging.getLogger(f"{LOGGER_ROOT}.{component}")


class SecretRedactionFilter(logging.Filter):
    """Mask secrets in the message text and in ``extra=`` fields of a record.

    The filter never drops records. It rewrites them so that a secret which was
    passed to the logger is not written by any handler.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = ()
        for name, value in list(vars(record).items()):
            if name in _STANDARD_ATTRS:
                continue
            if _SECRET_KEY_RE.search(name):
                setattr(record, name, REDACTED)
            elif isinstance(value, str):
                setattr(record, name, redact_text(value))
        return True


def configure(
    level: int | str = "INFO",
    *,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Attach one redacting stream handler to the ``treeos`` logger.

    Calling this again replaces the handler it installed earlier, so it is safe
    to call from several entry points. Handlers added by other code are kept.
    Returns the ``treeos`` root logger.
    """
    resolved = _resolve_level(level)
    root = logging.getLogger(LOGGER_ROOT)

    for handler in list(root.handlers):
        if getattr(handler, _HANDLER_MARK, False):
            root.removeHandler(handler)

    handler = logging.StreamHandler(stream)
    setattr(handler, _HANDLER_MARK, True)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    handler.addFilter(SecretRedactionFilter())
    root.addHandler(handler)
    root.setLevel(resolved)
    # Records are handled here, so do not also pass them to the global root
    # logger, which could print them unredacted.
    root.propagate = False
    return root


def _resolve_level(level: int | str) -> int:
    if isinstance(level, bool):
        raise ValueError("level must be a logging level name or number")
    if isinstance(level, int):
        if level < 0:
            raise ValueError(f"invalid logging level {level}")
        return level
    name = level.upper()
    if name not in _LEVELS:
        raise ValueError(f"unknown logging level {level!r}")
    resolved = logging.getLevelName(name)
    assert isinstance(resolved, int)
    return resolved
