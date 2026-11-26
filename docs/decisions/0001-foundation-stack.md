# 0001: Foundation stack

- **Status:** Accepted (recorded from [CLAUDE.md](../../CLAUDE.md) section 2)
- **Date:** 2026-11-26

## Context

TREE OS needs a fixed base so that components can be built and tested against
the same platform. CLAUDE.md section 2 is the source of truth for these choices.

## Decision

| Area | Choice |
| --- | --- |
| Distribution base | Ubuntu 24.04 LTS |
| Architecture | x86_64 |
| Init | systemd |
| Desktop | GNOME Shell and Mutter on Wayland (GNOME 46) |
| Shell customization | GNOME Shell extensions in GJS (ES modules) |
| Native apps | GTK4 with PyGObject, libadwaita where suitable |
| Services and apps language | Python 3 (Ubuntu 24.04 version) |
| System integration | D-Bus, GIO, systemd, Polkit |
| Audio / network / Bluetooth / power | PipeWire + WirePlumber / NetworkManager / BlueZ / UPower |
| Filesystem and bootloader | ext4 / GRUB |
| Packages | DEB and Flatpak |
| Testing | x86_64 Ubuntu 24.04 VM first; physical hardware only after approval |

## Consequences

- Changing any of these requires a documented proposal and owner approval.
- Sprint 001 tooling targets Python 3.12 (Ubuntu 24.04's version), so
  `pyproject.toml` sets `requires-python = ">=3.12"`.
