#!/usr/bin/env bash
# Install the TREE dock GNOME Shell extension for the current user.
#
# Copies desktop/shell/dock into the user's extensions directory, compiles the
# GSettings schema that ships with it, and enables the extension. Files are
# copied over the top of any previous install; nothing is deleted.
#
# Run this inside the GNOME 46 session (for example in the Ubuntu VM), then log
# out and back in so GNOME loads the extension. See docs/specifications/dock.md.
#
# Exit status: 0 on success, 1 on any failure, 2 on bad usage.

set -euo pipefail

readonly EXPECTED_UUID="tree-dock@treeos.org"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
source_dir="$repo_root/desktop/shell/dock"
extensions_root="${TREE_DOCK_EXTENSIONS_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/gnome-shell/extensions}"

enable_extension=1

usage() {
  cat <<'EOF'
Usage: install-dock-extension.sh [--no-enable] [--help]

  --no-enable   Install the files but do not enable the extension.
  --help        Show this message.

Environment:
  TREE_DOCK_EXTENSIONS_DIR  Override the install root (default:
                            $XDG_DATA_HOME/gnome-shell/extensions).
EOF
}

die() {
  printf 'install-dock-extension: error: %s\n' "$1" >&2
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --no-enable)
      enable_extension=0
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'install-dock-extension: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

# Check the source tree before touching the user's system.
for file in extension.js metadata.json pinned-apps.js stylesheet.css; do
  [ -f "$source_dir/$file" ] || die "missing $source_dir/$file"
done
[ -f "$source_dir/schemas/org.treeos.shell.dock.gschema.xml" ] \
  || die "missing GSettings schema in $source_dir/schemas"

# The install folder name must match the UUID in metadata.json.
uuid="$(sed -n 's/.*"uuid": *"\([^"]*\)".*/\1/p' "$source_dir/metadata.json")"
[ "$uuid" = "$EXPECTED_UUID" ] \
  || die "metadata.json UUID is '$uuid', expected '$EXPECTED_UUID'"

command -v glib-compile-schemas >/dev/null 2>&1 \
  || die "glib-compile-schemas not found; install libglib2.0-bin"
if [ "$enable_extension" -eq 1 ]; then
  command -v gnome-extensions >/dev/null 2>&1 \
    || die "gnome-extensions not found; install gnome-shell-extension-prefs or run with --no-enable"
fi

target_dir="$extensions_root/$uuid"
mkdir -p "$target_dir"
cp -R "$source_dir/." "$target_dir/"
echo "Copied extension files to $target_dir"

glib-compile-schemas "$target_dir/schemas"
echo "Compiled GSettings schema"

if [ "$enable_extension" -eq 1 ]; then
  if ! gnome-extensions enable "$uuid"; then
    die "files installed, but enabling $uuid failed; check that GNOME Shell is running"
  fi
  echo "Enabled $uuid"
fi

echo "Done. Log out and back in so GNOME Shell loads the extension."
