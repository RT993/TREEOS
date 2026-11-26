"""Static checks for the TREE dock extension metadata and GSettings schema.

These verify that the files agree with docs/specifications/dock.md. They do not
load the extension into GNOME Shell; that needs a running session (see the spec's
testing plan).
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCK_DIR = REPO_ROOT / "desktop" / "shell" / "dock"
SCHEMA_ID = "org.treeos.shell.dock"


def _metadata() -> dict[str, Any]:
    data: object = json.loads((DOCK_DIR / "metadata.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_metadata_declares_gnome_46_only() -> None:
    assert _metadata()["shell-version"] == ["46"]


def test_metadata_has_required_fields() -> None:
    meta = _metadata()
    for key in ("uuid", "name", "description", "settings-schema", "session-modes"):
        assert meta.get(key), f"metadata.json must set {key!r}"


def test_metadata_points_to_the_schema_id() -> None:
    assert _metadata()["settings-schema"] == SCHEMA_ID


def test_schema_declares_pinned_apps_as_string_array() -> None:
    root = ET.parse(DOCK_DIR / "schemas" / f"{SCHEMA_ID}.gschema.xml").getroot()
    schemas = root.findall("schema")
    assert [s.get("id") for s in schemas] == [SCHEMA_ID]
    keys = {key.get("name"): key for key in schemas[0].findall("key")}
    assert set(keys) == {"pinned-apps"}
    pinned = keys["pinned-apps"]
    assert pinned.get("type") == "as"
    default = pinned.findtext("default")
    assert default == "[]"


def test_pinned_apps_module_has_no_gnome_or_node_imports() -> None:
    source = (DOCK_DIR / "pinned-apps.js").read_text(encoding="utf-8")
    imports = re.findall(r"^\s*import\b.*$|\brequire\s*\(.*$", source, re.MULTILINE)
    for statement in imports:
        assert "gi://" not in statement, statement
        assert "resource://" not in statement, statement
        assert "node:" not in statement, statement
