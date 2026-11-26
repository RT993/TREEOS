# Contributing to TREE OS

Read [CLAUDE.md](CLAUDE.md) before making changes. It is the engineering contract
for this project.

## Workflow

1. Create a branch from `main`. Do not commit directly to `main`.
2. Make one focused change per commit, with a message in the form
   `type(scope): summary`, for example `feat(dock): add application pinning`.
3. Run `make check` and make sure it passes before you commit.
4. Update [CHANGELOG.md](CHANGELOG.md) and any affected docs.
5. Never commit secrets, ISO images, VM disks or other generated artifacts.

## Local checks

```bash
make venv    # one-time: creates .venv
make check   # ruff, mypy, pytest, shellcheck, eslint
```

Python tooling is installed only into `.venv`. Do not use `sudo pip` or modify
the system Python.

## Rules that always apply

- Physical installation, disk partitioning, formatting, bootloader changes and
  deleting user data require explicit approval from the project owner.
- Do not run privileged commands that modify the host without approval.
- A test is passing only if it was actually executed. Say so when it was not.
