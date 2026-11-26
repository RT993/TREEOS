// Pure logic for the TREE dock's pinned-application list.
//
// This module must not import GNOME (gi://) or Node APIs, so it can be tested
// outside a running shell. See docs/specifications/dock.md.

const DESKTOP_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._-]*\.desktop$/;

/**
 * Return true if `id` looks like a desktop-file ID (e.g. "org.gnome.Nautilus.desktop").
 * This checks the format only; whether the application is installed is checked elsewhere.
 *
 * @param {unknown} id
 * @returns {boolean}
 */
export function isValidDesktopId(id) {
  return typeof id === 'string' && id.length <= 255 && DESKTOP_ID_RE.test(id);
}

/**
 * Clean a stored list: keep valid IDs in their original order, with duplicates
 * removed silently. Invalid entries are dropped and returned in `dropped`, so
 * the caller can log them.
 *
 * @param {unknown} stored
 * @returns {{apps: string[], dropped: unknown[]}}
 */
export function normalizePinnedApps(stored) {
  if (!Array.isArray(stored)) {
    return {apps: [], dropped: stored === undefined ? [] : [stored]};
  }
  const apps = [];
  const dropped = [];
  for (const entry of stored) {
    if (!isValidDesktopId(entry)) {
      dropped.push(entry);
    } else if (!apps.includes(entry)) {
      apps.push(entry);
    }
  }
  return {apps, dropped};
}

/**
 * Return a new list with `id` appended. Pinning an already-pinned app is a no-op.
 *
 * @param {string[]} apps
 * @param {string} id
 * @returns {string[]}
 */
export function pinApp(apps, id) {
  if (!isValidDesktopId(id)) {
    throw new TypeError(`invalid desktop-file ID: ${String(id)}`);
  }
  return apps.includes(id) ? [...apps] : [...apps, id];
}

/**
 * Return a new list without `id`. Unpinning an app that is not pinned is a no-op.
 *
 * @param {string[]} apps
 * @param {string} id
 * @returns {string[]}
 */
export function unpinApp(apps, id) {
  return apps.filter(entry => entry !== id);
}
