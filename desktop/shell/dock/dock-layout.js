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
 * Geometry of the edge barrier that reveals an auto-hidden dock.
 *
 * `allowed` is the Mutter barrier direction for the inward direction from the
 * screen edge. The barrier is hit when the pointer tries to leave the screen
 * through that edge. The values follow GNOME's own barriers in js/ui/layout.js.
 *
 * @param {{x: number, y: number, width: number, height: number}} monitor
 * @param {string} position
 * @returns {{x1: number, y1: number, x2: number, y2: number, allowed: string}}
 */
export function barrierGeometry(monitor, position) {
  const edge = normalizePosition(position);
  const right = monitor.x + monitor.width;
  const bottom = monitor.y + monitor.height;

  if (edge === 'left') {
    return {x1: monitor.x, y1: monitor.y, x2: monitor.x, y2: bottom, allowed: 'POSITIVE_X'};
  }
  if (edge === 'right') {
    return {x1: right, y1: monitor.y, x2: right, y2: bottom, allowed: 'NEGATIVE_X'};
  }
  return {x1: monitor.x, y1: bottom, x2: right, y2: bottom, allowed: 'NEGATIVE_Y'};
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
