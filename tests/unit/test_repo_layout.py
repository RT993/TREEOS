"""Smoke tests that the Sprint 001 foundation files exist.

These guard the root documentation and tooling that the rest of the
project depends on. They do not test application behavior.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES: tuple[str, ...] = (
    "CLAUDE.md",
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "Makefile",
    ".gitignore",
    "pyproject.toml",
    "requirements-dev.txt",
    "package.json",
    "eslint.config.mjs",
    "docs/README.md",
    "docs/specifications/tree-config.md",
    "framework/tree-config/tree_config.py",
    ".github/workflows/ci.yml",
)


def test_required_foundation_files_exist() -> None:
    missing = [name for name in REQUIRED_FILES if not (REPO_ROOT / name).is_file()]
    assert missing == [], f"missing foundation files: {missing}"


def test_gitignore_excludes_secrets_and_envs() -> None:
    lines = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for pattern in (".env", "*.pem", "*.key", ".venv/", "node_modules/"):
        assert pattern in lines, f".gitignore must contain {pattern!r}"
