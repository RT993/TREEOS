// Unit tests for desktop/shell/dock/dock-layout.js, using Node's built-in test runner.
import assert from 'node:assert/strict';
import {describe, it} from 'node:test';

import {
  barrierGeometry,
  clampIconSize,
  dockPlacement,
  isVerticalPosition,
  normalizePosition,
} from '../../desktop/shell/dock/dock-layout.js';

const MONITOR = {x: 0, y: 0, width: 1920, height: 1080};

describe('clampIconSize', () => {
  it('keeps values inside the range', () => {
    assert.equal(clampIconSize(48), 48);
    assert.equal(clampIconSize(32), 32);
    assert.equal(clampIconSize(64), 64);
  });

  it('clamps values outside the range', () => {
    assert.equal(clampIconSize(8), 32);
    assert.equal(clampIconSize(500), 64);
  });

  it('rounds fractions and falls back to the default for non-numbers', () => {
    assert.equal(clampIconSize(40.6), 41);
    assert.equal(clampIconSize('big'), 48);
    assert.equal(clampIconSize(NaN), 48);
    assert.equal(clampIconSize(undefined), 48);
  });
});

describe('normalizePosition and isVerticalPosition', () => {
  it('accepts the three edges', () => {
    assert.equal(normalizePosition('bottom'), 'bottom');
    assert.equal(normalizePosition('left'), 'left');
    assert.equal(normalizePosition('right'), 'right');
  });

  it('falls back to bottom for unknown values', () => {
    assert.equal(normalizePosition('top'), 'bottom');
    assert.equal(normalizePosition(null), 'bottom');
  });

  it('treats left and right as vertical', () => {
    assert.equal(isVerticalPosition('bottom'), false);
    assert.equal(isVerticalPosition('left'), true);
    assert.equal(isVerticalPosition('right'), true);
  });
});

describe('barrierGeometry', () => {
  it('runs along the bottom edge and allows movement upward', () => {
    assert.deepEqual(barrierGeometry(MONITOR, 'bottom'), {
      x1: 0, y1: 1080, x2: 1920, y2: 1080, allowed: 'NEGATIVE_Y',
    });
  });

  it('runs along the left edge', () => {
    assert.deepEqual(barrierGeometry(MONITOR, 'left'), {
      x1: 0, y1: 0, x2: 0, y2: 1080, allowed: 'POSITIVE_X',
    });
  });

  it('runs along the right edge', () => {
    assert.deepEqual(barrierGeometry(MONITOR, 'right'), {
      x1: 1920, y1: 0, x2: 1920, y2: 1080, allowed: 'NEGATIVE_X',
    });
  });

  it('falls back to the bottom edge for an unknown position', () => {
    assert.deepEqual(barrierGeometry(MONITOR, 'top'), barrierGeometry(MONITOR, 'bottom'));
  });
});

describe('dockPlacement', () => {
  const dock = {width: 400, height: 80};

  it('centres the dock along the bottom edge with a margin', () => {
    assert.deepEqual(dockPlacement(MONITOR, dock, 'bottom'), {x: 760, y: 992});
  });

  it('places a left dock at the left edge, vertically centred', () => {
    const tall = {width: 80, height: 400};
    assert.deepEqual(dockPlacement(MONITOR, tall, 'left'), {x: 8, y: 340});
  });

  it('places a right dock at the right edge, vertically centred', () => {
    const tall = {width: 80, height: 400};
    assert.deepEqual(dockPlacement(MONITOR, tall, 'right'), {x: 1832, y: 340});
  });

  it('uses the monitor offset, not just the origin', () => {
    const offset = {x: 1920, y: 0, width: 1920, height: 1080};
    assert.deepEqual(dockPlacement(offset, dock, 'bottom'), {x: 2680, y: 992});
  });

  it('falls back to the bottom placement for an unknown edge', () => {
    assert.deepEqual(dockPlacement(MONITOR, dock, 'top'), dockPlacement(MONITOR, dock, 'bottom'));
  });
});
