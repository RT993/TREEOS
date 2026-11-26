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
