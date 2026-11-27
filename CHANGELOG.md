# Changelog

All notable changes to TREE OS are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- `CLAUDE.md` project engineering contract.
- Sprint 001 engineering foundation: `Makefile`, Python tooling config
  (`pyproject.toml`, `requirements-dev.txt`), JavaScript lint config
  (`package.json`, `eslint.config.mjs`), `.gitignore`, root documentation
  (`CONTRIBUTING.md`, `AGENTS.md`), `docs/` index, and a CI workflow.
- Foundation smoke tests in `tests/unit/`.
- `framework/tree-config`: schema-validated JSON configuration with atomic
  writes (`docs/specifications/tree-config.md`) and unit tests.
- TREE dock specification (`docs/specifications/dock.md`).
- Dock groundwork: GSettings schema `org.treeos.shell.dock`, extension
  metadata (GNOME 46 only), and a pure pinned-application list module with
  Node unit tests.
- TREE dock GNOME Shell extension (`desktop/shell/dock/extension.js`):
  pinned and running applications, click to launch or switch, a running
  indicator, and right-click Pin/Unpin/Quit. Verified manually in an
  Ubuntu 24.04 VM on GNOME Shell 46 (Wayland).
- Dock: unavailable pinned apps show an "is unavailable" tooltip on hover.
- Dock: a divider separates pinned apps from running apps when both are shown.
- Dock: icon size (32 to 64 px) and screen edge (bottom, left or right) are
  set through the `icon-size` and `position` GSettings keys. Placement logic is
  in `dock-layout.js` with Node tests. Side docks and reserved screen space are
  not yet verified in a GNOME session.
- Dock: optional auto-hide (`autohide` GSettings key). The dock fades out after
  the pointer leaves, and returns when the pointer reaches its screen edge or
  keyboard focus enters it. Built on Meta.Barrier. Not yet verified in a GNOME
  session.
