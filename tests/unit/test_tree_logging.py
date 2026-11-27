"""Unit tests for framework/tree-logging (docs/specifications/tree-logging.md)."""

from __future__ import annotations

import io
import logging
from collections.abc import Iterator

import pytest

from tree_logging import (
    LOGGER_ROOT,
    REDACTED,
    SecretRedactionFilter,
    configure,
    get_logger,
    redact_text,
)


@pytest.fixture(autouse=True)
def _reset_treeos_logger() -> Iterator[None]:
    root = logging.getLogger(LOGGER_ROOT)
    saved_handlers = list(root.handlers)
    saved_level = root.level
    saved_propagate = root.propagate
    yield
    for handler in list(root.handlers):
        root.removeHandler(handler)
    for handler in saved_handlers:
        root.addHandler(handler)
    root.setLevel(saved_level)
    root.propagate = saved_propagate


def _capture(level: int | str = "DEBUG") -> io.StringIO:
    stream = io.StringIO()
    configure(level, stream=stream)
    return stream


# --- get_logger -------------------------------------------------------------


def test_get_logger_uses_component_namespace() -> None:
    logger = get_logger("tree-config")
    assert logger.name == "treeos.tree-config"


@pytest.mark.parametrize("name", ["", "Tree", "1config", "a/b", "../x", "a b"])
def test_get_logger_rejects_invalid_component_names(name: str) -> None:
    with pytest.raises(ValueError, match="invalid component name"):
        get_logger(name)


# --- configure -------------------------------------------------------------


def test_configure_writes_records_with_level_and_name() -> None:
    stream = _capture("INFO")
    get_logger("settings").info("ready")
    line = stream.getvalue()
    assert "INFO treeos.settings: ready" in line


def test_configure_filters_below_level() -> None:
    stream = _capture("WARNING")
    logger = get_logger("settings")
    logger.info("quiet")
    logger.warning("loud")
    assert "quiet" not in stream.getvalue()
    assert "loud" in stream.getvalue()


def test_configure_accepts_numeric_and_lowercase_levels() -> None:
    stream = _capture(logging.ERROR)
    get_logger("settings").warning("hidden")
    assert stream.getvalue() == ""
    root = configure("error", stream=stream)
    assert root.level == logging.ERROR


@pytest.mark.parametrize("level", ["VERBOSE", "", True, -1])
def test_configure_rejects_invalid_levels(level: int | str) -> None:
    with pytest.raises(ValueError):
        configure(level, stream=io.StringIO())


def test_configure_is_idempotent() -> None:
    first = io.StringIO()
    second = io.StringIO()
    configure("INFO", stream=first)
    configure("INFO", stream=second)
    get_logger("settings").info("once")
    assert first.getvalue() == ""
    assert "once" in second.getvalue()
    tree_handlers = [
        h
        for h in logging.getLogger(LOGGER_ROOT).handlers
        if getattr(h, "_treeos_handler", False)
    ]
    assert len(tree_handlers) == 1


def test_configure_keeps_handlers_added_by_others() -> None:
    root = logging.getLogger(LOGGER_ROOT)
    other = logging.NullHandler()
    root.addHandler(other)
    configure("INFO", stream=io.StringIO())
    assert other in root.handlers


def test_configure_does_not_propagate_to_global_root() -> None:
    root = configure("INFO", stream=io.StringIO())
    assert root.propagate is False


# --- redaction ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("password=hunter2", f"password={REDACTED}"),
        ("token: abc.def.ghi", f"token: {REDACTED}"),
        ("api_key = 'xyz 123'", f"api_key = '{REDACTED}'"),
        ('secret="s3cr3t value"', f'secret="{REDACTED}"'),
        ("API-KEY=k1, user=bob", f"API-KEY={REDACTED}, user=bob"),
        ("private_key=PEMDATA;next", f"private_key={REDACTED};next"),
    ],
)
def test_redact_text_masks_secret_values(text: str, expected: str) -> None:
    assert redact_text(text) == expected


def test_redact_text_leaves_ordinary_text_alone() -> None:
    text = "mounted /dev/disk-free at 42% (tokens are not secrets here)"
    assert redact_text(text) == text


def test_logged_message_is_redacted() -> None:
    stream = _capture("INFO")
    get_logger("auth").info("login failed, password=hunter2 user=bob")
    output = stream.getvalue()
    assert "hunter2" not in output
    assert f"password={REDACTED}" in output
    assert "user=bob" in output


def test_redacted_format_arguments_are_masked() -> None:
    stream = _capture("INFO")
    get_logger("auth").info("bad credentials: %s", "token=abc123")
    output = stream.getvalue()
    assert "abc123" not in output
    assert f"token={REDACTED}" in output


def test_extra_fields_with_secret_names_are_masked() -> None:
    record = logging.LogRecord("treeos.x", logging.INFO, "", 0, "hi", None, None)
    setattr(record, "api_key", "zzz")  # noqa: B010
    setattr(record, "route", "/x")  # noqa: B010
    assert SecretRedactionFilter().filter(record) is True
    assert getattr(record, "api_key") == REDACTED  # noqa: B009
    assert getattr(record, "route") == "/x"  # noqa: B009


def test_extra_string_values_are_redacted_too() -> None:
    record = logging.LogRecord("treeos.x", logging.INFO, "", 0, "hi", None, None)
    setattr(record, "detail", "password=oops")  # noqa: B010
    assert SecretRedactionFilter().filter(record) is True
    assert getattr(record, "detail") == f"password={REDACTED}"  # noqa: B009


def test_filter_never_drops_records() -> None:
    record = logging.LogRecord("treeos.x", logging.INFO, "", 0, "plain", None, None)
    assert SecretRedactionFilter().filter(record) is True
    assert record.getMessage() == "plain"
