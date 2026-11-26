# TREE OS --- Claude Code Project Instructions

> **Project:** TREE OS\
> **Instruction file:** `CLAUDE.md`\
> **Version:** 1.0\
> **Base distribution:** Ubuntu 24.04 LTS\
> **Target architecture:** x86_64\
> **Desktop foundation:** GNOME 46 / Mutter / Wayland\
> **Primary hardware target:** MacBook Air 2017 (Intel)\
> **Development strategy:** Virtual machine first; physical installation
> only after explicit approval

These instructions are the engineering contract for Claude Code working
in this repository. Read this file before making changes. Follow it
together with the architecture decisions and specifications in `docs/`.

------------------------------------------------------------------------

# 1. Project mission

TREE OS is an independent Ubuntu-based Linux distribution with a
polished, macOS-inspired desktop experience and an integrated set of
desktop applications and system services.

The project aims to provide:

-   A coherent desktop with a top panel, dock, launcher, workspaces and
    quick settings.
-   A Finder-inspired file manager.
-   Centralized system settings.
-   Universal local search.
-   System monitoring.
-   Backup and restore.
-   Software and update management.
-   A consistent visual design system.
-   A reproducible bootable ISO and installer.
-   Reliable support for the target Intel MacBook Air hardware.

TREE OS must remain a genuine Linux distribution. Do not represent it as
macOS, use Apple's proprietary code or assets, or promise exact
compatibility with proprietary Apple services.

## Engineering priorities

In descending order:

1.  Correctness and data safety.
2.  Security.
3.  Stability and recoverability.
4.  Hardware compatibility.
5.  Accessibility and usability.
6.  Performance.
7.  Visual polish and animation.

Do not sacrifice the higher priorities to improve a lower one.

------------------------------------------------------------------------

# 2. Non-negotiable project decisions

Unless the project owner explicitly changes them, preserve these
decisions:

  -----------------------------------------------------------------------
  Area                                Decision
  ----------------------------------- -----------------------------------
  Distribution base                   Ubuntu 24.04 LTS

  CPU architecture                    x86_64 for the initial release

  Kernel                              Supported Ubuntu kernel packages

  Init and service manager            systemd

  Desktop foundation                  GNOME Shell and Mutter

  Display protocol                    Wayland

  Desktop shell customization         GNOME Shell extensions

  Native application toolkit          GTK4

  Application design system           libadwaita where appropriate, with
                                      TREE styling

  Shell extension language            GJS / JavaScript ES modules

  Application and service language    Python 3

  System integration                  D-Bus, GIO, systemd, Polkit

  Audio                               ALSA, PipeWire and WirePlumber

  Networking                          NetworkManager

  Bluetooth                           BlueZ

  Battery and power information       UPower and systemd-logind

  Default filesystem                  ext4

  Bootloader                          GRUB

  Package formats                     DEB and Flatpak

  Source control                      Git

  Initial testing                     x86_64 Ubuntu virtual machine

  Physical installation               Prohibited without explicit user
                                      authorization
  -----------------------------------------------------------------------

Do not silently change the Ubuntu release, desktop foundation,
application toolkit, architecture or package strategy. If a change
appears necessary, explain the reason, alternatives, migration impact
and risks, then request approval.

------------------------------------------------------------------------

# 3. Required working method

Work as a careful software engineering team. Do not attempt to generate
the entire operating system in one operation.

For every task:

1.  Read this file and the relevant documentation.
2.  Inspect the current repository and Git status.
3.  Identify the exact component and its dependencies.
4.  Check the existing implementation before creating new files.
5.  Write a short implementation plan.
6.  Define or confirm interfaces before implementing cross-component
    behavior.
7.  Implement one coherent, reviewable increment.
8.  Add or update tests.
9.  Run the relevant tests and static checks.
10. Review the diff for unintended changes.
11. Update documentation and changelog when appropriate.
12. Report the outcome honestly.

Do not start unrelated tasks unless explicitly asked.

## Task sizing

Prefer small, independently verifiable changes. A task should normally
change one component or one tightly related group of files.

If a request is too large for one safe change:

-   Break it into ordered subtasks.
-   Identify dependencies.
-   Complete the first useful increment.
-   Report what remains.

Do not claim that a multi-stage feature is complete when only its
interface, mock-up or placeholder exists.

------------------------------------------------------------------------

# 4. Repository architecture

Use the existing repository structure. The intended high-level layout
is:

``` text
tree-os/
├── CLAUDE.md
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── Makefile
├── docs/
│   ├── architecture/
│   ├── specifications/
│   ├── development/
│   └── decisions/
├── branding/
│   ├── logos/
│   ├── icons/
│   ├── wallpapers/
│   ├── fonts/
│   ├── themes/
│   └── sounds/
├── desktop/
│   ├── shell/
│   │   ├── dock/
│   │   ├── top-panel/
│   │   ├── launcher/
│   │   ├── control-center/
│   │   ├── window-overview/
│   │   └── search-provider/
│   ├── theme/
│   └── session/
├── framework/
│   ├── tree-ui/
│   ├── tree-settings/
│   ├── tree-config/
│   ├── tree-dbus/
│   ├── tree-logging/
│   └── tree-utils/
├── applications/
│   ├── finder/
│   ├── settings/
│   ├── search/
│   ├── monitor/
│   ├── backup/
│   ├── store/
│   ├── update/
│   ├── connect/
│   ├── welcome/
│   ├── terminal/
│   └── browser/
├── services/
│   ├── power/
│   ├── notifications/
│   ├── indexing/
│   ├── backup/
│   ├── update/
│   └── device-monitor/
├── system/
│   ├── packages/
│   ├── systemd/
│   ├── dbus/
│   ├── polkit/
│   ├── udev/
│   ├── network/
│   ├── audio/
│   └── hardware/
│       └── apple/
├── distro/
│   ├── package-lists/
│   ├── default-config/
│   ├── default-applications/
│   ├── branding/
│   ├── installer/
│   ├── first-boot/
│   └── release/
├── packaging/
│   ├── debian/
│   ├── flatpak/
│   ├── metapackages/
│   └── repository/
├── build/
│   ├── scripts/
│   ├── image/
│   ├── iso/
│   ├── dependencies/
│   └── manifests/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── desktop/
│   ├── system/
│   ├── hardware/
│   ├── security/
│   └── acceptance/
├── tools/
└── .github/
    └── workflows/
```

Do not create empty directories just to reproduce this tree unless the
current task requires them. Keep the repository understandable and avoid
unnecessary scaffolding.

## Dependency direction

Follow this dependency direction:

-   `framework` must not depend on individual applications.
-   Applications may depend on `framework`.
-   Services may use framework utilities but must not depend on
    application UI code.
-   Desktop shell extensions must not import Python application
    internals.
-   Applications must not directly manipulate the GNOME Shell process.
-   Distribution and packaging layers assemble components; they should
    not contain application business logic.

Avoid circular dependencies. If two components need to communicate,
define a documented interface or D-Bus contract.

------------------------------------------------------------------------

# 5. Technology and implementation standards

## 5.1 GNOME Shell extensions

Use GJS and the GNOME Shell extension APIs available in GNOME 46 on
Ubuntu 24.04.

Requirements:

-   Use ES modules and the supported extension structure.
-   Declare extension metadata accurately.
-   Implement lifecycle methods correctly.
-   Clean up signals, actors, sources, timers and other resources in
    `disable()`.
-   Avoid monkey-patching GNOME Shell internals.
-   Avoid private or undocumented APIs where a supported alternative
    exists.
-   Keep each extension focused on one responsibility.
-   Provide preferences through supported extension mechanisms.
-   Test enabling, disabling, restarting the shell session and
    upgrading.
-   Do not assume that an extension compatible with a newer GNOME
    release is compatible with GNOME 46.

Do not modify Mutter or fork GNOME Shell unless the project owner
approves a documented architectural change.

## 5.2 GTK applications

Use GTK4 with PyGObject for Python desktop applications.

Use libadwaita components where they provide suitable behavior and
accessibility. Apply TREE styling through a shared design system without
creating brittle global CSS overrides.

Requirements:

-   Follow GTK application lifecycle conventions.
-   Use GIO for filesystem and application integration.
-   Use asynchronous APIs for operations that could block the UI.
-   Keep UI code separate from business logic.
-   Provide keyboard navigation and accessible labels.
-   Handle errors visibly and safely.
-   Avoid blocking the main event loop.
-   Use standard desktop portals where appropriate.

## 5.3 Python

-   Target the Python version supplied by Ubuntu 24.04 unless a
    documented compatibility reason requires otherwise.
-   Add type hints to public functions and important internal
    interfaces.
-   Follow PEP 8.
-   Use Ruff for linting and formatting.
-   Use pytest for tests.
-   Use mypy where practical.
-   Prefer the standard library and existing system libraries.
-   Avoid unnecessary dependencies.
-   Do not use `sudo pip`.
-   Do not modify Ubuntu's externally managed system Python environment.
-   Use virtual environments for development-only Python dependencies.
-   Handle exceptions deliberately; do not hide errors with broad empty
    exception handlers.

## 5.4 JavaScript

-   Use GJS-compatible JavaScript.
-   Use ES modules.
-   Apply consistent formatting and linting.
-   Avoid browser-only APIs unless the runtime explicitly provides them.
-   Manage object and signal lifetimes carefully.
-   Avoid global mutable state.
-   Do not assume Node.js APIs are available in GJS.

## 5.5 Shell scripts

-   Use Bash where Bash is required.
-   Use safe quoting and explicit error handling.
-   Run ShellCheck.
-   Validate arguments.
-   Avoid destructive defaults.
-   Never use an unreviewed `curl | sh` pattern.
-   Do not use wildcard deletion or disk-writing commands without
    explicit safeguards.
-   Scripts must report actionable errors and return meaningful exit
    codes.

------------------------------------------------------------------------

# 6. System integration contracts

Use existing Linux services instead of creating competing
implementations.

  Function                   Preferred system component
  -------------------------- ----------------------------
  Network configuration      NetworkManager
  Bluetooth                  BlueZ
  Audio routing              PipeWire / WirePlumber
  Hardware audio interface   ALSA
  Battery information        UPower
  Session and power events   systemd-logind
  Service management         systemd
  Filesystem integration     GIO / GVfs
  Privilege authorization    Polkit
  Application isolation      Flatpak and portals
  Firewall                   UFW / nftables
  Package management         APT and Flatpak

Do not directly edit system-managed configuration files when a supported
D-Bus API or management interface exists.

Do not create multiple services that control the same resource. For
example, do not combine competing power-management daemons without
documenting and testing their interaction.

------------------------------------------------------------------------

# 7. D-Bus and inter-process communication

Use D-Bus for well-defined communication between TREE applications and
services.

Proposed namespaces:

``` text
com.treeos.Desktop
com.treeos.Settings
com.treeos.Search
com.treeos.Backup
com.treeos.Update
com.treeos.DeviceMonitor
```

These are proposed names, not permission to create incomplete or
unstable APIs.

Before implementing a D-Bus service:

1.  Document its purpose.
2.  Define methods, signals and properties.
3.  Define argument and return types.
4.  Define error behavior.
5.  Define authorization requirements.
6.  Consider API versioning.
7.  Add integration tests.
8.  Document compatibility expectations.

Never expose privileged operations through an unauthenticated D-Bus
method. Use Polkit and narrowly scoped privileged helpers where
required.

Validate all inputs received through D-Bus.

------------------------------------------------------------------------

# 8. TREE design system

TREE OS should have a consistent, original visual identity inspired by
the usability and interaction patterns of macOS.

Visual direction:

-   Dark graphite as the initial default theme.
-   Optional light theme.
-   Subtle translucency where supported.
-   Restrained shadows and blur.
-   Consistent rounded corners.
-   Clear typography and hierarchy.
-   Consistent spacing.
-   Smooth but restrained animations.
-   High-contrast and accessibility options.
-   Consistent application icons.

Do not copy Apple's logos, icons, wallpapers, sounds, fonts or
proprietary assets. Use original assets or assets with compatible
licenses.

Define reusable design tokens for:

-   Colors.
-   Typography.
-   Spacing.
-   Corner radii.
-   Elevation.
-   Motion.
-   Icon sizes.
-   Component states.

Applications must use shared TREE components instead of independently
inventing their own visual systems.

Visual polish must not reduce responsiveness or accessibility. Respect
reduced-motion settings.

------------------------------------------------------------------------

# 9. Application specifications

Implement applications incrementally. A visible control must perform its
advertised action or be clearly marked as unavailable or planned.

## TREE Finder

Expected functionality:

-   Home and standard user directories.
-   Sidebar and favorites.
-   Icon, list and column views where practical.
-   Breadcrumb navigation.
-   Tabs and multiple windows.
-   Search and sorting.
-   File copy, move, rename and delete.
-   Trash handling.
-   External volume browsing.
-   Network locations through supported GIO/GVfs backends.
-   File previews.
-   Archive integration.
-   Hidden-file visibility.
-   Progress and error reporting.

Use GIO and established Linux filesystem interfaces. Do not reimplement
filesystem semantics.

## TREE Settings

Expected sections:

-   Appearance.
-   Desktop and workspaces.
-   Displays.
-   Sound.
-   Network.
-   Bluetooth.
-   Keyboard.
-   Trackpad.
-   Power.
-   Privacy.
-   Users.
-   Storage.
-   Updates.
-   About.

Settings must call the appropriate system service. Do not show controls
that cannot change the underlying system state.

## TREE Search

Expected search targets:

-   Installed applications.
-   Local files and folders.
-   Recent documents.
-   Settings.
-   Calculator expressions.
-   Supported system actions.

Search must be local-first, cancellable, incremental and configurable.
Avoid indexing private or excluded locations without user consent.

## TREE Monitor

Expected information:

-   CPU.
-   Memory.
-   Storage.
-   Network.
-   Processes.
-   Process search and termination.
-   Startup applications.
-   Temperatures where supported by hardware interfaces.

Do not invent sensor values or claim that unavailable hardware metrics
are supported.

## TREE Backup

Use a mature backup engine such as BorgBackup rather than writing a new
backup format.

Expected functionality:

-   Local backup destinations.
-   Optional network destinations.
-   Encryption.
-   Retention policies.
-   Backup status.
-   Snapshot browsing.
-   File restoration.
-   Integrity and failure reporting.

Test restores, not just backup creation. Never delete older backups
until the retention operation has been verified.

## TREE Store and TREE Update

Use supported package-management interfaces.

Requirements:

-   Respect package signatures.
-   Preserve package-manager locks.
-   Obtain authorization for privileged operations.
-   Display progress and errors.
-   Avoid concurrent conflicting package operations.
-   Never silently remove unrelated packages.
-   Provide a recovery path for interrupted operations.

## TREE Welcome and installer

Use Ubuntu's established installer infrastructure as the starting point.

Do not create a custom partitioning or bootloader-writing implementation
unless there is a compelling documented reason and a dedicated test
plan.

The installer must clearly identify target disks and destructive
actions. Require explicit confirmation before erasing or repartitioning
a disk.

------------------------------------------------------------------------

# 10. Hardware compatibility

The initial physical target is a 2017 Intel MacBook Air. Do not assume
every machine in that model family has identical components.

Before making hardware-specific changes, collect and inspect:

``` bash
sudo dmidecode -s system-product-name
sudo dmidecode -s system-version
lspci -nnk
lsusb
inxi -Fxxxz
sudo lshw -short
```

Use these commands for diagnosis only. Do not assume a particular Wi-Fi,
Bluetooth, audio or trackpad chipset before inspecting the machine.

Hardware areas to validate:

-   Intel CPU and integrated graphics.
-   Wi-Fi and firmware.
-   Bluetooth.
-   Keyboard and keyboard backlight.
-   Trackpad and gestures.
-   Speakers and microphone.
-   Webcam.
-   Battery reporting and charging.
-   Suspend and resume.
-   Thermal behavior.
-   USB and Thunderbolt.
-   External displays.

For every hardware-specific change, document:

1.  Hardware identifier.
2.  Driver or firmware source.
3.  Ubuntu package dependency.
4.  Reason for the change.
5.  Installation steps.
6.  Removal steps.
7.  Rollback procedure.
8.  Physical test evidence.

Do not install unverified kernel patches or third-party drivers simply
because a tutorial recommends them.

A virtual machine cannot prove physical hardware compatibility.

------------------------------------------------------------------------

# 11. Security and data protection

Security requirements apply to every component.

## Mandatory rules

-   Never run a normal desktop application as root.
-   Never store passwords, tokens or private keys in plaintext
    configuration.
-   Never commit secrets to Git.
-   Never disable Ubuntu security updates.
-   Never bypass APT signature verification.
-   Never install untrusted packages.
-   Never execute remote scripts automatically.
-   Never expose network services without a documented requirement.
-   Validate all external input.
-   Use Polkit for privileged operations.
-   Use least privilege for services.
-   Use systemd sandboxing where compatible.
-   Use atomic writes for important configuration.
-   Require confirmation for destructive operations.
-   Log security-relevant failures without leaking secrets.

## Sensitive operations

The following require explicit user authorization before execution:

-   Disk partitioning.
-   Formatting filesystems.
-   Writing bootloaders.
-   Installing to physical hardware.
-   Deleting user data.
-   Removing system packages outside an approved build environment.
-   Changing host networking or firewall policy.
-   Changing host boot configuration.
-   Running privileged commands that modify the host.

Do not infer authorization from a general request to develop TREE OS.

------------------------------------------------------------------------

# 12. Build and development safety

The initial development environment must be an x86_64 Ubuntu 24.04
virtual machine.

Suggested starting allocation:

-   4 virtual CPU cores.
-   4--6 GB RAM.
-   64 GB virtual disk.
-   UEFI firmware.
-   NAT networking.
-   Graphics acceleration where available.

Adjust resources to the host's capacity.

## Host protection

-   Work inside the TREE OS repository.
-   Keep build artifacts in designated build directories.
-   Do not modify the host OS.
-   Do not write an ISO to a physical disk.
-   Do not run installation commands against the host.
-   Do not mount or modify host partitions.
-   Use VM snapshots before risky experiments.
-   Verify the target of every disk-related command.
-   Prefer disposable virtual disks for installer testing.

Never assume that `/dev/sda`, `/dev/nvme0n1` or any other device name
refers to a safe test disk.

------------------------------------------------------------------------

# 13. Testing and quality gates

Every component must include tests appropriate to its behavior.

## Python

-   pytest.
-   Ruff linting and formatting checks.
-   mypy where practical.
-   Tests for errors, invalid input and edge cases.

## JavaScript / GJS

-   ESLint or an equivalent compatible lint setup.
-   GNOME Shell extension validation.
-   Lifecycle tests.
-   Manual session testing where automation is insufficient.

## Shell

-   ShellCheck.
-   Bats tests where appropriate.
-   Safe argument and failure-path tests.

## Packages

-   Build verification.
-   Lintian.
-   Dependency checks.
-   Install, upgrade and removal tests.
-   Autopkgtest where appropriate.

## Integration

Test:

-   D-Bus service startup and shutdown.
-   Polkit authorization.
-   Configuration persistence.
-   Network and audio integration.
-   Application launch.
-   Error and recovery paths.

## ISO and system acceptance

Before a release candidate:

-   Boot the ISO in UEFI mode.
-   Verify live-session startup.
-   Complete installation to a disposable virtual disk.
-   Create and log into a user account.
-   Verify desktop startup.
-   Test applications and services.
-   Test update behavior.
-   Test backup and restore.
-   Test recovery documentation.
-   Check system logs for critical errors.
-   Run a security review.

Do not report a test as passed unless it was actually executed. Clearly
distinguish automated tests, manual tests, untested behavior and blocked
tests.

------------------------------------------------------------------------

# 14. Definition of done

A component is complete only when all applicable conditions are
satisfied:

-   Its behavior matches its specification.
-   No critical controls are placeholders.
-   Code is readable and maintainable.
-   Error cases are handled.
-   Accessibility has been considered.
-   Tests have been added.
-   Relevant tests pass.
-   Static checks pass.
-   Dependencies are documented.
-   Installation and removal behavior are documented.
-   User-facing documentation is updated.
-   Known limitations are recorded.
-   The Git diff contains no unrelated changes.

A mock-up is not a functional application. A successful build is not
proof of runtime correctness. A successful VM test is not proof of
physical hardware compatibility.

------------------------------------------------------------------------

# 15. Git and change management

Use small, focused commits.

Suggested commit format:

``` text
feat(dock): add application pinning
fix(finder): handle missing mount points
test(settings): cover invalid configuration
docs(architecture): document search service
build(iso): add reproducible image manifest
```

Before committing:

1.  Inspect `git status`.
2.  Review the full diff.
3.  Run relevant tests.
4.  Check for secrets and generated files.
5.  Confirm no unrelated user changes are included.

Never reset, discard, overwrite or rewrite user changes without explicit
permission.

Do not force-push or rewrite shared Git history unless explicitly
authorized.

------------------------------------------------------------------------

# 16. Release engineering

TREE OS releases must be reproducible and traceable.

Every release should record:

-   TREE OS version.
-   Ubuntu base and point-release source.
-   Kernel package version.
-   GNOME Shell version.
-   Package manifest.
-   Build environment.
-   Source commit.
-   Build logs.
-   Test results.
-   Known issues.
-   ISO checksum.
-   Signing information where applicable.

The distribution must have a documented update and support strategy.

Ubuntu 24.04 LTS is the selected initial base. Plan a tested migration
to a later supported Ubuntu LTS before the standard maintenance period
ends. Do not perform an in-place base upgrade without a dedicated
migration project and test plan.

------------------------------------------------------------------------

# 17. Required response format after every task

At the end of each task, provide:

## Implementation summary

What was actually implemented.

## Files created

List new files and their purpose.

## Files modified

List changed files and why.

## Dependencies

List dependencies added, removed or changed.

## Commands executed

List important commands actually run.

## Tests

For each test, report: - Command or procedure. - Passed, failed, blocked
or not run. - Relevant output or reason.

## Security and data impact

State whether the change affects privileges, user data, networking,
packages or boot behavior.

## Limitations

List incomplete functionality and known risks.

## Next step

Recommend one logical next task.

Never claim that the entire operating system is complete after
completing a single component.

------------------------------------------------------------------------

# 18. Initial project execution

When first opening this repository:

1.  Read this file.
2.  Inspect the repository tree.
3.  Inspect Git status.
4.  Read all existing architecture decisions and specifications.
5.  Identify missing documentation.
6.  Report inconsistencies between files.
7.  Propose a foundation implementation plan.

Do not immediately implement the dock, Finder, Settings or ISO.

The first approved development milestone is **Sprint 001 --- Engineering
Foundation**.

Sprint 001 should establish:

-   Repository structure.
-   Root project documentation.
-   Development conventions.
-   Python and JavaScript tooling.
-   Test framework configuration.
-   Git ignore rules.
-   Initial Makefile.
-   Initial CI checks.
-   Development environment verification.

Do not build an ISO during Sprint 001.

Do not install TREE OS on physical hardware during Sprint 001.

------------------------------------------------------------------------

# 19. Final engineering principle

TREE OS must be a real, maintainable operating system project.

**Correctness before speed.**\
**Stability before animation.**\
**Security before convenience.**\
**Modularity before shortcuts.**\
**Verified functionality before claims.**

When uncertain, inspect the code, consult the official documentation,
explain the uncertainty and choose the safest reversible approach.

Do not guess. Do not fabricate. Do not hide failures.
