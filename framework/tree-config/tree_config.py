"""Schema-validated, atomically written configuration files.

See docs/specifications/tree-config.md for the contract this module implements.
This module uses only the standard library and must not import application or
service code (CLAUDE.md section 4).
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

__all__ = [
    "ConfigError",
    "Field",
    "Schema",
    "Value",
    "config_path",
    "load",
    "save",
]

type Value = bool | int | str
type Kind = Literal["bool", "int", "str"]

_KINDS: Final[frozenset[str]] = frozenset({"bool", "int", "str"})
_NAME_RE: Final[re.Pattern[str]] = re.compile(r"[a-z][a-z0-9-]*")


class ConfigError(Exception):
    """Raised for every expected configuration failure."""


@dataclass(frozen=True)
class Field:
    """Definition of one configuration key."""

    kind: Kind
    default: Value
    minimum: int | None = None
    maximum: int | None = None
    choices: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        if self.kind not in _KINDS:
            raise ConfigError(f"unknown field kind {self.kind!r}")
        if self.kind != "int" and (
            self.minimum is not None or self.maximum is not None
        ):
            raise ConfigError("minimum and maximum are only valid for int fields")
        if self.kind != "str" and self.choices is not None:
            raise ConfigError("choices are only valid for str fields")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ConfigError("minimum is greater than maximum")
        try:
            self.check(self.default, key="default")
        except ConfigError as exc:
            raise ConfigError(f"invalid default: {exc}") from exc

    def check(self, value: object, *, key: str) -> Value:
        """Return ``value`` if it is valid for this field, otherwise raise."""
        if self.kind == "bool":
            if not isinstance(value, bool):
                raise ConfigError(f"{key}: expected a boolean, got {value!r}")
            return value
        if self.kind == "int":
            # bool is a subclass of int in Python, so exclude it explicitly.
            if isinstance(value, bool) or not isinstance(value, int):
                raise ConfigError(f"{key}: expected an integer, got {value!r}")
            if self.minimum is not None and value < self.minimum:
                raise ConfigError(f"{key}: {value} is below the minimum {self.minimum}")
            if self.maximum is not None and value > self.maximum:
                raise ConfigError(f"{key}: {value} is above the maximum {self.maximum}")
            return value
        if not isinstance(value, str):
            raise ConfigError(f"{key}: expected a string, got {value!r}")
        if self.choices is not None and value not in self.choices:
            raise ConfigError(f"{key}: {value!r} is not one of {list(self.choices)}")
        return value


type Schema = Mapping[str, Field]


def _defaults(schema: Schema) -> dict[str, Value]:
    return {key: field.default for key, field in schema.items()}


def _validate(schema: Schema, values: Mapping[str, object]) -> dict[str, Value]:
    """Check every key in ``values`` against ``schema`` and fill in defaults."""
    unknown = sorted(set(values) - set(schema))
    if unknown:
        raise ConfigError(f"unknown configuration keys: {', '.join(unknown)}")
    result = _defaults(schema)
    for key, raw in values.items():
        result[key] = schema[key].check(raw, key=key)
    return result


def config_path(name: str) -> Path:
    """Return the configuration file path for ``name``.

    Uses ``$XDG_CONFIG_HOME/treeos/<name>.json``, falling back to
    ``~/.config/treeos/<name>.json`` when ``XDG_CONFIG_HOME`` is unset or empty.
    """
    if not _NAME_RE.fullmatch(name):
        raise ConfigError(
            f"invalid configuration name {name!r}: use lowercase letters, digits "
            "and hyphens, starting with a letter"
        )
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "treeos" / f"{name}.json"


def load(path: Path, schema: Schema) -> dict[str, Value]:
    """Load and validate the configuration at ``path``.

    A missing file yields the schema defaults. The file is never modified.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _defaults(schema)
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    try:
        data: object = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path} is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top-level value must be a JSON object")
    try:
        return _validate(schema, data)
    except ConfigError as exc:
        raise ConfigError(f"{path}: {exc}") from exc


def save(path: Path, schema: Schema, values: Mapping[str, object]) -> None:
    """Validate ``values`` and write them to ``path`` atomically.

    Nothing is written if validation fails. The target is replaced in a single
    ``os.replace`` call, so readers see either the old or the new file.
    """
    try:
        checked = _validate(schema, values)
    except ConfigError as exc:
        raise ConfigError(f"refusing to save {path}: {exc}") from exc

    payload = json.dumps(checked, indent=2, sort_keys=True) + "\n"
    directory = path.parent
    temp_name: str | None = None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=directory,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        temp_name = None
        _fsync_directory(directory)
    except OSError as exc:
        raise ConfigError(f"cannot write {path}: {exc}") from exc
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except OSError:
                # The original error is already being reported; a leftover
                # temporary file is not worth masking it.
                pass


def _fsync_directory(directory: Path) -> None:
    """Flush directory metadata so the rename survives a crash."""
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
