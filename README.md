# TREEOS

A hobbyist OS for every computer.

TREE OS is an independent Linux distribution based on Ubuntu 24.04 LTS, with a
macOS-inspired desktop built on GNOME Shell, Mutter and Wayland. It is a Linux
distribution, not macOS, and it does not use Apple's proprietary code or assets.

## Status

Early engineering. Sprint 001 (Engineering Foundation) sets up tooling, the
repository layout and CI checks. There is no installable ISO yet, and no desktop
or application features are implemented.

## Project rules

[CLAUDE.md](CLAUDE.md) is the engineering contract for this repository. It covers
the non-negotiable technology decisions, security rules, testing gates and the
approval process for sensitive operations, such as installing to hardware.

## Development

Requirements: Ubuntu 24.04 LTS (x86_64) is the target development environment.
Python 3.12 and Node.js 20 or later are needed for the checks.

```bash
make venv    # create .venv with development-only Python tools
make check   # run ruff, mypy, pytest, shellcheck and eslint
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and [docs/](docs/README.md)
for architecture decisions.

## License

Not yet decided.
