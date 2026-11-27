// Pure layout logic for the TREE dock: icon size and screen edge.
//
// This module must not import GNOME (gi://) or Node APIs, so it can be tested
// outside a running shell. See docs/specifications/dock.md.

export const MIN_ICON_SIZE = 32;
export const MAX_ICON_SIZE = 64;
export const DEFAULT_ICON_SIZE = 48;
export const POSITIONS = ['bottom', 'left', 'right'];
export const DEFAULT_POSITION = 'bottom';

const EDGE_MARGIN = 8;

/**
 * Return a usable icon size. Non-integers and out-of-range values are clamped
 * into the allowed range, or replaced by the default when they are not numbers.
 *
 * @param {unknown} value
 * @returns {number}
 */
export function clampIconSize(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return DEFAULT_ICON_SIZE;
  }
  return Math.min(MAX_ICON_SIZE, Math.max(MIN_ICON_SIZE, Math.round(value)));
}

/**
 * Return a known screen edge. Anything else falls back to the bottom edge.
 *
 * @param {unknown} value
 * @returns {'bottom'|'left'|'right'}
 */
export function normalizePosition(value) {
  return POSITIONS.includes(value) ? value : DEFAULT_POSITION;
}

/**
 * True when the dock's items run top to bottom (side docks).
 *
 * @param {string} position
 * @returns {boolean}
 */
export function isVerticalPosition(position) {
  return normalizePosition(position) !== 'bottom';
}

/**
 * Work out where the dock's top-left corner goes on a monitor.
 *
 * The dock is centred along its edge, with a fixed margin from the edge.
 *
 * @param {{x: number, y: number, width: number, height: number}} monitor
 * @param {{width: number, height: number}} dock
 * @param {string} position
 * @returns {{x: number, y: number}}
 */
export function dockPlacement(monitor, dock, position) {
  const edge = normalizePosition(position);
  const centredX = monitor.x + Math.floor((monitor.width - dock.width) / 2);
  const centredY = monitor.y + Math.floor((monitor.height - dock.height) / 2);

  if (edge === 'left') {
    return {x: monitor.x + EDGE_MARGIN, y: centredY};
  }
  if (edge === 'right') {
    return {x: monitor.x + monitor.width - dock.width - EDGE_MARGIN, y: centredY};
  }
  return {x: centredX, y: monitor.y + monitor.height - dock.height - EDGE_MARGIN};
}
