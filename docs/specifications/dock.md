# Specification: TREE dock

- **Component:** `desktop/shell/dock`
- **Status:** Draft. No code has been written. Open questions are listed at the end and need owner decisions before implementation.
- **Platform:** Ubuntu 24.04 LTS, GNOME Shell 46, Mutter on Wayland, x86_64

## Purpose

The dock is a persistent bar of application launchers, with a running indicator for
each open application. It is provided as a GNOME Shell extension, because CLAUDE.md
section 2 fixes GNOME Shell extensions as the shell customization mechanism.

This spec defines the first increment only. It does not cover the top panel,
launcher, control center or window overview, which need their own specs.

## Scope

In scope for the first increment:

- Showing pinned applications and currently running applications.
- Launching a pinned or running application on click.
- Pinning and unpinning an application from its context menu.
- A running indicator for applications with open windows.
- Storing the pinned list in the user's configuration.
- Showing the dock on the primary monitor only.

Out of scope for the first increment, to be specified later:

- Multi-monitor placement and per-monitor docks.
- Auto-hide and position settings.
- Drag-and-drop reordering.
- Badges and notification counts.
- Window previews on hover.
- Integration with TREE Settings.

## Components and boundaries

| Part | Responsibility | Dependency rule |
| --- | --- | --- |
| Shell extension (`desktop/shell/dock`) | Draws the dock inside GNOME Shell and handles clicks. | GJS only. Must not import Python application code (CLAUDE.md section 4). |
| Pinned-app store | Reads and writes the list of pinned application IDs. | Uses the GNOME `Gio.Settings` schema shipped with the extension, not a custom file. |

The pinned-app list is stored through GSettings, not through `tree-config`. The
`tree-config` module is a Python framework component, and the shell extension
cannot use it. GSettings is the supported GNOME mechanism for extension
preferences (CLAUDE.md section 5.1).

Applications are identified by their desktop-file ID, for example
`org.gnome.Nautilus.desktop`. Lookups go through `Gio.DesktopAppInfo`, which is the
supported API for application metadata.

## Interface

### GSettings schema

Schema ID: `org.treeos.shell.dock`

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `pinned-apps` | `as` | `[]` | Desktop-file IDs of pinned applications, in display order. |

Writes must validate that every entry names an installed application. An entry
that is no longer installed is kept in the list, marked unavailable, and is not
launched. It is removed only when the user unpins it.

### Extension lifecycle

- `enable()` creates the dock actor, connects to the signals it needs, and adds
  the actor to the primary monitor's layout.
- `disable()` disconnects every signal, removes the actor, and releases every
  timer and source. Nothing may remain after disable (CLAUDE.md section 5.1).
- The extension must survive shell restart and session restart without leaking
  resources.

### Metadata

`metadata.json` declares `shell-version: ["46"]` only. Versions other than 46 are
not declared, because compatibility with other GNOME releases is not tested
(CLAUDE.md section 5.1).

## Behavior

1. A pinned application is shown even when it is not running.
2. A running application that is not pinned is shown after the pinned ones, and
   disappears when its last window closes.
3. Clicking a running application activates its most recent window. Clicking a
   stopped application launches it.
4. A pinned application that is not installed is shown greyed out with an
   "unavailable" tooltip. Clicking it does nothing else.
5. The context menu offers Pin or Unpin, and Quit only for running applications.
6. Pinning or unpinning takes effect immediately and is saved to GSettings.

## Accessibility and motion

- Every item has an accessible name equal to the application's display name.
- Items are reachable with the keyboard, and Enter activates them.
- Running indicators are not conveyed by colour alone. They are a separate
  shape and have a text-equivalent in the accessible description.
- Any animation respects the GNOME `enable-animations` setting. When animations
  are disabled, state changes happen instantly.

## Failure handling

- If an application cannot be launched, the dock shows a notification with the
  application name and the error. It does not fail silently.
- If GSettings contains an invalid value, the dock falls back to an empty list and
  logs the problem. It does not crash the shell.

## Testing plan

| Test | Type | Where it runs |
| --- | --- | --- |
| Lint of all extension JavaScript | ESLint with GJS globals | `make check` |
| Metadata and schema validation (JSON parses, shell-version is 46, schema keys match this spec) | Automated | `make check` |
| Lifecycle: enable, disable, enable again, with no leaked signals | Requires a GNOME Shell session | VM, manual or scripted |
| Pinning, unpinning and launch behaviour | Requires a GNOME Shell session | VM, manual |
| Restart of the shell session with pinned apps persisted | Requires a GNOME Shell session | VM, manual |
| Keyboard navigation and accessible names | Requires a GNOME Shell session | VM, manual with Orca |

Lifecycle and interaction tests need a running GNOME 46 session in the Ubuntu VM.
Until that session exists, those tests are **not run**, and the dock is not
reported as working.

## Limitations

- The first increment works on the primary monitor only.
- GNOME Shell extensions run inside the shell process. A bug in the dock can
  crash the session, so the disable path is tested before any feature is
  considered complete.
- Only GNOME 46 is supported.

## Open questions for the owner

1. **Desktop environment in the VM.** Testing needs GNOME Shell 46 installed in
   the Ubuntu VM. That is a `sudo apt install` of several gigabytes and is a host
   change, so it needs your approval and your password entered by you.
2. **Pinned list storage.** GSettings is proposed, because it is the GNOME
   mechanism. The alternative is `tree-config`. This needs a decision, because
   the two conflict.
3. **Default pinned apps.** The spec proposes an empty default. Should the
   first-boot defaults come from `distro/default-applications/`, and which
   applications should they be?
4. **Next increments.** After the first increment, the spec proposes the top
   panel as the next shell component. Confirm the order before it is written.
