// Unit tests for desktop/shell/dock/pinned-apps.js, using Node's built-in test runner.
// The module under test has no GNOME or Node-specific dependencies.
import assert from 'node:assert/strict';
import {describe, it} from 'node:test';

import {
  isValidDesktopId,
  normalizePinnedApps,
  pinApp,
  unpinApp,
} from '../../desktop/shell/dock/pinned-apps.js';

describe('isValidDesktopId', () => {
  it('accepts typical desktop-file IDs', () => {
    assert.equal(isValidDesktopId('org.gnome.Nautilus.desktop'), true);
    assert.equal(isValidDesktopId('firefox_esr-1.desktop'), true);
  });

  it('rejects paths, missing suffix and non-strings', () => {
    assert.equal(isValidDesktopId('../etc/passwd.desktop'), false);
    assert.equal(isValidDesktopId('/usr/share/app.desktop'), false);
    assert.equal(isValidDesktopId('firefox'), false);
    assert.equal(isValidDesktopId('app.desktop '), false);
    assert.equal(isValidDesktopId(42), false);
    assert.equal(isValidDesktopId(null), false);
  });

  it('rejects IDs longer than 255 characters', () => {
    assert.equal(isValidDesktopId(`${'a'.repeat(250)}.desktop`), false);
  });
});

describe('normalizePinnedApps', () => {
  it('keeps valid unique entries in order', () => {
    const result = normalizePinnedApps([
      'b.desktop',
      'a.desktop',
      'b.desktop',
    ]);
    assert.deepEqual(result, {apps: ['b.desktop', 'a.desktop'], dropped: []});
  });

  it('drops invalid entries and reports them', () => {
    const result = normalizePinnedApps(['ok.desktop', '../bad', 7]);
    assert.deepEqual(result, {apps: ['ok.desktop'], dropped: ['../bad', 7]});
  });

  it('treats a non-array as an empty list and reports it', () => {
    assert.deepEqual(normalizePinnedApps('ok.desktop'), {
      apps: [],
      dropped: ['ok.desktop'],
    });
  });

  it('treats undefined as an empty list without reporting', () => {
    assert.deepEqual(normalizePinnedApps(undefined), {apps: [], dropped: []});
  });
});

describe('pinApp and unpinApp', () => {
  it('appends a new app without changing the input', () => {
    const before = ['a.desktop'];
    const after = pinApp(before, 'b.desktop');
    assert.deepEqual(after, ['a.desktop', 'b.desktop']);
    assert.deepEqual(before, ['a.desktop']);
  });

  it('pinning an already pinned app is a no-op', () => {
    assert.deepEqual(pinApp(['a.desktop'], 'a.desktop'), ['a.desktop']);
  });

  it('refuses invalid IDs', () => {
    assert.throws(() => pinApp([], '../x'), TypeError);
  });

  it('removes an app and ignores apps that are not pinned', () => {
    assert.deepEqual(unpinApp(['a.desktop', 'b.desktop'], 'a.desktop'), ['b.desktop']);
    assert.deepEqual(unpinApp(['a.desktop'], 'z.desktop'), ['a.desktop']);
  });
});
