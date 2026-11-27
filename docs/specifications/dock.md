# Specification: TREE dock

- **Component:** `desktop/shell/dock`
- **Status:** Draft. Pinned-list storage is decided (GSettings). Remaining open questions are at the end.
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

Out of scope for the first increment:

- Multi-monitor placement and per-monitor docks.
- Integration with TREE Settings.
- Everything in the second increment below, which is planned but not built.
- Everything in the deferred list below.

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

## Second increment (planned, not implemented)

This section specifies the macOS-style dock features that are planned after the
first increment. Nothing in this section is implemented yet. Each feature is a
separate, reviewable change, built in the order below. A feature is not reported
as working until its manual tests in the GNOME 46 VM are run.

### Feature order

1. Divider between pinned and running applications.
2. Icon size and screen edge (bottom, left, right).
3. Auto-hide.
4. Magnification on hover.
5. Drag to reorder pinned applications.
6. Attention highlight for applications that request attention.
7. Trash item and Downloads folder item.

### Additional GSettings keys

Schema `org.treeos.shell.dock` gains these keys. Existing keys do not change.

| Key | Type | Default | Meaning |
| --- | --- | --- | --- |
| `icon-size` | `i` | `48` | Icon size in pixels. Valid range 32 to 64. Other values are clamped and logged. |
| `position` | `s` | `'bottom'` | Screen edge: `bottom`, `left` or `right`. Other values fall back to `bottom` and are logged. |
| `autohide` | `b` | `false` | Hide the dock when the pointer is away from it. |
| `magnification` | `b` | `false` | Enlarge icons near the pointer. Has no effect when animations are disabled. |

### Behaviour of each feature

1. **Divider.** A thin separator sits between the pinned group and the running
   group, but only when both groups have items. It is decorative: it is not
   focusable and has no accessible name. It is drawn with a shape, not colour alone.
2. **Icon size and edge.** The dock is placed on the primary monitor's chosen edge
   and centred along it. Changing `icon-size` or `position` takes effect at once.
   Side docks reserve their space on the side, not the bottom. Placement is
   calculated by a pure function that is tested without GNOME.
3. **Auto-hide.** When enabled, the dock slides out of view after the pointer
   leaves it. It is shown again when the pointer reaches the screen edge where the
   dock sits. The edge trigger is removed in `disable()`. With animations disabled,
   the dock appears and disappears instantly. The implementation must confirm that
   the GNOME 46 edge-trigger API is supported; if it is not, auto-hide is not built.
4. **Magnification.** While the pointer is over the dock, icons near it grow by up
   to 1.5 times, with the growth falling off with distance. Scaling uses actor
   scale, not layout changes, so neighbouring icons do not jump. When GNOME
   animations are disabled, magnification is off regardless of the setting.
5. **Reordering.** A pinned icon can be dragged to another pinned position. The new
   order is written to `pinned-apps` in one change. Running applications cannot be
   dragged in this increment. Moving an item uses a pure function, `moveApp`, in
   `pinned-apps.js`, which is tested without GNOME. Dropping an invalid ID is
   refused, as for pinning.
6. **Attention.** When a window of an application asks for attention and is not
   focused, the application's icon is highlighted. With animations enabled it also
   moves up and down three times. The highlight stops when the window is focused.
   The display signal for attention requests must be confirmed against the GNOME 46
   API in the VM before this feature is built.
7. **Trash and Downloads.** Both are fixed items at the end of the dock, after a
   divider. The Trash item uses GIO's `trash:///` location and shows an empty or
   full icon from GIO's trash state. Clicking either item opens the location with
   the user's default file handler. If no handler exists, the dock shows a
   notification. "Empty Trash" is **not** in this increment, because it is
   destructive and would need a confirmation dialog. The Downloads stack popup is
   also not in this increment; the item opens the folder only.

### Accessibility and motion for the second increment

- Every new control has an accessible name: "Trash" and "Downloads".
- Auto-hide and magnification must not hide an item from keyboard focus. Focusing
  an item with the keyboard brings the dock on screen.
- Motion (auto-hide slide, magnification, attention bounce) is off when the GNOME
  `enable-animations` setting is off.

### Testing for the second increment

| Test | Type | Where it runs |
| --- | --- | --- |
| `moveApp` and placement calculation for each edge and size | Node unit tests | `make check` |
| GSettings schema keys and ranges | Automated | `make check` |
| Divider, edge placement and icon size on a real screen | GNOME session | VM, manual |
| Auto-hide triggers, including keyboard focus | GNOME session | VM, manual |
| Magnification and attention highlight, with animations on and off | GNOME session | VM, manual |
| Trash and Downloads open, and the no-handler notification | GNOME session | VM, manual |
| Enable, disable and re-enable with auto-hide on, with no leaked edge trigger | GNOME session | VM, manual |

### Deferred (not planned for the second increment)

- **Badges and notification counts.** They need a notification service, which
  has no specification yet.
- **Window previews on hover.** These need their own specification.
- **Genie effect for minimize-to-dock.** This needs changes to Mutter's window
  animations. CLAUDE.md section 5.1 forbids that without the owner's approval.
- **Empty Trash and the Downloads stack popup.** Listed above as later work.

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
2. **Pinned list storage.** Decided: GSettings (`org.treeos.shell.dock`), because it
   is the GNOME mechanism for extension preferences.
3. **Default pinned apps.** The spec proposes an empty default. Should the
   first-boot defaults come from `distro/default-applications/`, and which
   applications should they be?
4. **Next increments.** After the first increment, the spec proposes the top
   panel as the next shell component. Confirm the order before it is written.
5. **Second-increment order.** The feature order above is a proposal. Confirm it,
   and whether auto-hide should wait until the edge-trigger API is verified in the
   VM.
6. **Trash target.** Until the Finder exists, the Trash and Downloads items open
   with the default handler. Confirm that is acceptable, or name a fallback.
