"""Unit tests for framework/tree-config (docs/specifications/tree-config.md)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

import pytest

from tree_config import ConfigError, Field, config_path, load, save

SCHEMA: dict[str, Field] = {
    "dark_mode": Field(kind="bool", default=True),
    "font_size": Field(kind="int", default=12, minimum=6, maximum=72),
    "theme": Field(kind="str", default="graphite", choices=("graphite", "light")),
    "label": Field(kind="str", default=""),
}


def write_json(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --- load -------------------------------------------------------------------


def test_missing_file_returns_defaults(tmp_path: Path) -> None:
    values = load(tmp_path / "absent.json", SCHEMA)
    assert values == {
        "dark_mode": True,
        "font_size": 12,
        "theme": "graphite",
        "label": "",
    }


def test_load_fills_missing_keys_with_defaults(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    write_json(path, '{"font_size": 20}')
    values = load(path, SCHEMA)
    assert values["font_size"] == 20
    assert values["dark_mode"] is True


def test_load_does_not_modify_file(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    write_json(path, '{"font_size": 20}')
    before = path.read_bytes()
    load(path, SCHEMA)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "text, fragment",
    [
        ("{not json", "not valid JSON"),
        ("[]", "top-level value must be a JSON object"),
        ('"text"', "top-level value must be a JSON object"),
    ],
)
def test_load_rejects_malformed_documents(
    tmp_path: Path, text: str, fragment: str
) -> None:
    path = tmp_path / "c.json"
    write_json(path, text)
    with pytest.raises(ConfigError, match=fragment):
        load(path, SCHEMA)


def test_load_rejects_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    write_json(path, '{"font_siz": 20}')
    with pytest.raises(ConfigError, match="unknown configuration keys: font_siz"):
        load(path, SCHEMA)


@pytest.mark.parametrize(
    "text, key",
    [
        ('{"dark_mode": 1}', "dark_mode"),
        ('{"dark_mode": "yes"}', "dark_mode"),
        ('{"font_size": "20"}', "font_size"),
        ('{"font_size": 20.5}', "font_size"),
        ('{"theme": 3}', "theme"),
    ],
)
def test_load_rejects_wrong_types(tmp_path: Path, text: str, key: str) -> None:
    path = tmp_path / "c.json"
    write_json(path, text)
    with pytest.raises(ConfigError, match=key):
        load(path, SCHEMA)


def test_bool_is_not_accepted_as_int(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    write_json(path, '{"font_size": true}')
    with pytest.raises(ConfigError, match="expected an integer"):
        load(path, SCHEMA)


def test_load_enforces_bounds(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    write_json(path, '{"font_size": 5}')
    with pytest.raises(ConfigError, match="below the minimum 6"):
        load(path, SCHEMA)
    write_json(path, '{"font_size": 73}')
    with pytest.raises(ConfigError, match="above the maximum 72"):
        load(path, SCHEMA)


def test_load_enforces_choices(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    write_json(path, '{"theme": "neon"}')
    with pytest.raises(ConfigError, match="not one of"):
        load(path, SCHEMA)


def test_unreadable_non_utf8_file_is_config_error(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_bytes(b"\xff\xfe\x00bad")
    with pytest.raises(ConfigError, match="cannot read"):
        load(path, SCHEMA)


# --- save -------------------------------------------------------------------


def test_save_then_load_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "dir" / "c.json"
    save(path, SCHEMA, {"font_size": 18, "theme": "light"})
    assert load(path, SCHEMA) == {
        "dark_mode": True,
        "font_size": 18,
        "theme": "light",
        "label": "",
    }


def test_save_writes_sorted_json_object(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    save(path, SCHEMA, {"label": "x"})
    data = json.loads(path.read_text(encoding="utf-8"))
    assert list(data) == sorted(data)
    assert data["label"] == "x"


def test_save_refuses_invalid_values_and_writes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    with pytest.raises(ConfigError, match="refusing to save"):
        save(path, SCHEMA, {"font_size": 1000})
    assert not path.exists()


def test_save_refuses_unknown_keys_and_keeps_old_file(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    save(path, SCHEMA, {"font_size": 14})
    before = path.read_bytes()
    with pytest.raises(ConfigError, match="unknown configuration keys"):
        save(path, SCHEMA, {"nope": 1})
    assert path.read_bytes() == before


def test_save_leaves_no_temporary_files_on_success(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    save(path, SCHEMA, {"font_size": 14})
    save(path, SCHEMA, {"font_size": 15})
    assert sorted(p.name for p in tmp_path.iterdir()) == ["c.json"]


def test_failed_replace_removes_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "c.json"

    def fail_replace(src: str, dst: Path) -> None:
        raise OSError("simulated crash before rename")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(ConfigError, match="cannot write"):
        save(path, SCHEMA, {"font_size": 14})
    assert not path.exists()
    assert list(tmp_path.iterdir()) == []


def test_failed_replace_keeps_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "c.json"
    save(path, SCHEMA, {"font_size": 14})
    before = path.read_bytes()

    def fail_replace(src: str, dst: Path) -> None:
        raise OSError("simulated failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(ConfigError):
        save(path, SCHEMA, {"font_size": 20})
    assert path.read_bytes() == before


# --- schema validation ------------------------------------------------------


@pytest.mark.parametrize(
    "build",
    [
        lambda: Field(kind="float", default=1.0),  # type: ignore[arg-type]
        lambda: Field(kind="bool", default=True, minimum=1),
        lambda: Field(kind="int", default=1, minimum=5, maximum=2),
        lambda: Field(kind="str", default="a", minimum=1),
        lambda: Field(kind="str", default="a", choices=("b",)),
        lambda: Field(kind="int", default=99, maximum=10),
        lambda: Field(kind="bool", default=1),
    ],
)
def test_invalid_field_definitions_are_rejected(build: Callable[[], Field]) -> None:
    with pytest.raises(ConfigError):
        build()


# --- config_path ------------------------------------------------------------


def test_config_path_uses_xdg_config_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert config_path("desktop") == tmp_path / "treeos" / "desktop.json"


def test_config_path_falls_back_to_home_when_xdg_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", "")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert config_path("desktop") == tmp_path / ".config" / "treeos" / "desktop.json"


@pytest.mark.parametrize(
    "name", ["", "Desktop", "1abc", "a/b", "../etc", "a b", "a_b", "-x"]
)
def test_config_path_rejects_invalid_names(name: str) -> None:
    with pytest.raises(ConfigError, match="invalid configuration name"):
        config_path(name)
