// TREE dock: a GNOME Shell 46 extension showing pinned and running applications.
// See docs/specifications/dock.md for the behaviour this file implements.

import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Meta from 'gi://Meta';
import Shell from 'gi://Shell';
import St from 'gi://St';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

import {
  isValidDesktopId,
  normalizePinnedApps,
  pinApp,
  unpinApp,
} from './pinned-apps.js';
import {
  DEFAULT_ICON_SIZE,
  DEFAULT_POSITION,
  barrierGeometry,
  clampIconSize,
  dockPlacement,
  isVerticalPosition,
  normalizePosition,
} from './dock-layout.js';

const INDICATOR_SIZE = 5;
const UNAVAILABLE_OPACITY = 102; // 40% of 255
const PINNED_KEY = 'pinned-apps';
const ICON_SIZE_KEY = 'icon-size';
const POSITION_KEY = 'position';
const AUTOHIDE_KEY = 'autohide';
const FALLBACK_ICON = 'application-x-executable';
const TOOLTIP_GAP = 6;
const DIVIDER_WIDTH = 1;
const HIDE_DELAY_MS = 500;
const FADE_MS = 200;
const SHOWN_OPACITY = 255;
const HIDDEN_OPACITY = 0;
const INTERFACE_SCHEMA = 'org.gnome.desktop.interface';

// Mutter barrier directions, keyed by the names used in dock-layout.js.
const BARRIER_DIRECTIONS = {
  POSITIVE_X: Meta.BarrierDirection.POSITIVE_X,
  NEGATIVE_X: Meta.BarrierDirection.NEGATIVE_X,
  NEGATIVE_Y: Meta.BarrierDirection.NEGATIVE_Y,
};

class TreeDock {
  constructor(settings) {
    this._settings = settings;
    this._appSystem = Shell.AppSystem.get_default();
    this._interfaceSettings = new Gio.Settings({schema_id: INTERFACE_SCHEMA});
    this._signalIds = [];
    this._actor = null;
    this._menu = null;
    this._menuManager = null;
    this._tooltip = null;
    this._iconSize = DEFAULT_ICON_SIZE;
    this._position = DEFAULT_POSITION;
    this._autohide = false;
    this._barrier = null;
    this._barrierHitId = 0;
    this._hideTimeoutId = 0;
    this._hidden = false;
  }

  enable() {
    this._actor = new St.BoxLayout({
      style_class: 'tree-dock',
      vertical: false,
    });
    Main.layoutManager.addChrome(this._actor, {
      affectsStruts: true,
      trackFullscreen: true,
    });
    this._actor.connect('enter-event', () => {
      this._cancelHide();
      return Clutter.EVENT_PROPAGATE;
    });
    this._actor.connect('leave-event', () => {
      this._scheduleHide();
      return Clutter.EVENT_PROPAGATE;
    });

    this._connect(this._settings, `changed::${PINNED_KEY}`, () => this.rebuild());
    this._connect(this._settings, `changed::${ICON_SIZE_KEY}`, () => this.rebuild());
    this._connect(this._settings, `changed::${POSITION_KEY}`, () => this.rebuild());
    this._connect(this._settings, `changed::${AUTOHIDE_KEY}`, () => this.rebuild());
    this._connect(this._appSystem, 'app-state-changed', () => this.rebuild());
    this._connect(this._appSystem, 'installed-changed', () => this.rebuild());
    this._connect(Main.layoutManager, 'monitors-changed', () => this._reposition());

    this.rebuild();
  }

  disable() {
    for (const [object, id] of this._signalIds) {
      object.disconnect(id);
    }
    this._signalIds = [];

    this._cancelHide();
    this._removeBarrier();
    this._closeMenu();
    this._hideTooltip();
    if (this._actor !== null) {
      Main.layoutManager.removeChrome(this._actor);
      this._actor.destroy();
      this._actor = null;
    }
    this._hidden = false;
  }

  rebuild() {
    if (this._actor === null) {
      return;
    }
    this._closeMenu();
    this._hideTooltip();
    this._actor.destroy_all_children();

    this._iconSize = clampIconSize(this._settings.get_int(ICON_SIZE_KEY));
    this._position = normalizePosition(this._settings.get_string(POSITION_KEY));
    this._autohide = this._settings.get_boolean(AUTOHIDE_KEY);
    this._actor.vertical = isVerticalPosition(this._position);

    const stored = this._settings.get_strv(PINNED_KEY);
    const {apps: pinned, dropped} = normalizePinnedApps(stored);
    if (dropped.length > 0) {
      console.warn(`tree-dock: ignoring invalid pinned-apps entries: ${JSON.stringify(dropped)}`);
    }

    for (const id of pinned) {
      this._actor.add_child(this._buildItem(id, true));
    }

    const running = this._appSystem
      .get_running()
      .filter(app => app.get_id() !== null && !pinned.includes(app.get_id()));
    if (pinned.length > 0 && running.length > 0) {
      this._actor.add_child(this._buildDivider());
    }
    for (const app of running) {
      this._actor.add_child(this._buildItem(app.get_id(), false));
    }

    this._reposition();
  }

  // Decorative separator. St.Widget is not focusable and has no accessible
  // name, so it is ignored by keyboard navigation and screen readers.
  _buildDivider() {
    // A vertical dock has a horizontal line between groups, and the reverse.
    const vertical = isVerticalPosition(this._position);
    return new St.Widget({
      style_class: 'tree-dock-divider',
      width: vertical ? this._iconSize : DIVIDER_WIDTH,
      height: vertical ? DIVIDER_WIDTH : this._iconSize,
      x_align: Clutter.ActorAlign.CENTER,
      y_align: Clutter.ActorAlign.CENTER,
    });
  }

  _connect(object, signal, callback) {
    this._signalIds.push([object, object.connect(signal, callback)]);
  }

  _buildItem(id, pinned) {
    const app = this._appSystem.lookup_app(id);
    const name = app !== null ? app.get_name() : id;

    const icon = app !== null
      ? app.create_icon_texture(this._iconSize)
      : new St.Icon({icon_name: FALLBACK_ICON, icon_size: this._iconSize});

    const column = new St.BoxLayout({vertical: true});
    column.add_child(icon);

    const isRunning = app !== null && app.get_windows().length > 0;
    if (isRunning) {
      // A fixed-size, centred dot. Without the explicit size and alignment the
      // widget stretches across the column.
      column.add_child(new St.Widget({
        style_class: 'tree-dock-indicator',
        width: INDICATOR_SIZE,
        height: INDICATOR_SIZE,
        x_align: Clutter.ActorAlign.CENTER,
      }));
    }

    const button = new St.Button({
      style_class: 'tree-dock-item',
      can_focus: true,
      track_hover: true,
      reactive: true,
      child: column,
    });
    button.get_accessible().set_name(name);
    // Text accessible descriptions are not set yet. Calling set_description on
    // the button's accessible object throws a TypeError on GNOME 46, which stops
    // the whole extension from loading. Restore it once the correct API is
    // confirmed in the VM.

    if (app === null) {
      // Dimmed by actor opacity (0-255), not CSS, so it applies reliably in St.
      button.add_style_class_name('tree-dock-item-unavailable');
      button.opacity = UNAVAILABLE_OPACITY;
      button.connect('enter-event', () => {
        this._showTooltip(button, `${name} is unavailable`);
        return Clutter.EVENT_PROPAGATE;
      });
      button.connect('leave-event', () => {
        this._hideTooltip();
        return Clutter.EVENT_PROPAGATE;
      });
    }

    // Keyboard focus must bring a hidden dock back, so a user can reach it.
    button.connect('key-focus-in', () => {
      this._showDock();
      return Clutter.EVENT_PROPAGATE;
    });

    button.connect('clicked', () => this._activate(app, name));
    button.connect('button-press-event', (_actor, event) => {
      if (event.get_button() === Clutter.BUTTON_SECONDARY) {
        this._showMenu(button, id, app, pinned);
        return Clutter.EVENT_STOP;
      }
      return Clutter.EVENT_PROPAGATE;
    });

    return button;
  }

  _activate(app, name) {
    if (app === null) {
      // Pinned but not installed: shown as unavailable and does nothing.
      return;
    }
    try {
      app.activate();
    } catch (error) {
      console.error(`tree-dock: failed to start ${name}: ${error}`);
      Main.notify(`Could not start ${name}`, String(error.message ?? error));
    }
  }

  _showMenu(button, id, app, pinned) {
    this._closeMenu();

    const name = app !== null ? app.get_name() : id;
    const menu = new PopupMenu.PopupMenu(button, 0.5, St.Side.TOP);
    Main.uiGroup.add_child(menu.actor);
    this._menuManager = new PopupMenu.PopupMenuManager(button);
    this._menuManager.addMenu(menu);
    this._menu = menu;

    if (pinned) {
      menu.addAction(`Unpin ${name}`, () => this._setPinned(id, false));
    } else if (app !== null) {
      menu.addAction(`Pin ${name}`, () => this._setPinned(id, true));
    }

    if (app !== null && app.get_windows().length > 0) {
      menu.addAction(`Quit ${name}`, () => app.request_quit());
    }

    menu.open();
  }

  _showTooltip(button, text) {
    this._hideTooltip();
    const label = new St.Label({style_class: 'tree-dock-tooltip', text});
    Main.uiGroup.add_child(label);
    this._tooltip = label;

    const [x, y] = button.get_transformed_position();
    const [, width] = label.get_preferred_width(-1);
    const [, height] = label.get_preferred_height(-1);
    const left = Math.floor(x + (button.get_width() - width) / 2);
    label.set_position(left, Math.floor(y - height - TOOLTIP_GAP));
  }

  _hideTooltip() {
    if (this._tooltip !== null) {
      this._tooltip.destroy();
      this._tooltip = null;
    }
  }

  _closeMenu() {
    if (this._menu !== null) {
      this._menu.close();
      this._menu.destroy();
      this._menu = null;
    }
    this._menuManager = null;
  }

  _setPinned(id, pin) {
    if (!isValidDesktopId(id)) {
      console.warn(`tree-dock: refusing to pin invalid ID ${JSON.stringify(id)}`);
      return;
    }
    const current = normalizePinnedApps(this._settings.get_strv(PINNED_KEY)).apps;
    const next = pin ? pinApp(current, id) : unpinApp(current, id);
    this._settings.set_strv(PINNED_KEY, next);
  }

  _reposition() {
    const monitor = Main.layoutManager.primaryMonitor;
    if (monitor === null || this._actor === null) {
      return;
    }
    const [, width] = this._actor.get_preferred_width(-1);
    const [, height] = this._actor.get_preferred_height(-1);
    const {x, y} = dockPlacement(monitor, {width, height}, this._position);
    this._actor.set_position(x, y);
    this._updateBarrier();
  }

  // Auto-hide: an edge barrier reveals the dock, and it hides again after the
  // pointer has been away for HIDE_DELAY_MS. Without auto-hide the dock is
  // always visible and the barrier is removed.
  _updateBarrier() {
    this._removeBarrier();
    if (!this._autohide) {
      this._cancelHide();
      this._setVisible(true);
      return;
    }

    const monitor = Main.layoutManager.primaryMonitor;
    if (monitor === null) {
      return;
    }
    const geometry = barrierGeometry(monitor, this._position);
    this._barrier = new Meta.Barrier({
      backend: global.backend,
      x1: geometry.x1,
      y1: geometry.y1,
      x2: geometry.x2,
      y2: geometry.y2,
      directions: BARRIER_DIRECTIONS[geometry.allowed],
    });
    this._barrierHitId = this._barrier.connect('hit', () => this._showDock());
    this._scheduleHide();
  }

  _removeBarrier() {
    if (this._barrier !== null) {
      this._barrier.disconnect(this._barrierHitId);
      this._barrier.destroy();
      this._barrier = null;
      this._barrierHitId = 0;
    }
  }

  _showDock() {
    this._cancelHide();
    if (this._hidden) {
      this._setVisible(true);
    }
  }

  _hideDock() {
    // Keep the dock open while a menu from it is showing.
    if (this._autohide && !this._hidden && this._menu === null) {
      this._setVisible(false);
    }
  }

  _scheduleHide() {
    this._cancelHide();
    if (!this._autohide) {
      return;
    }
    this._hideTimeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, HIDE_DELAY_MS, () => {
      this._hideTimeoutId = 0;
      this._hideDock();
      return GLib.SOURCE_REMOVE;
    });
  }

  _cancelHide() {
    if (this._hideTimeoutId !== 0) {
      GLib.source_remove(this._hideTimeoutId);
      this._hideTimeoutId = 0;
    }
  }

  // A hidden dock is not reactive, so the pointer reaches the barrier instead.
  // The fade follows GNOME's enable-animations setting: with animations off the
  // change is instant.
  _setVisible(visible) {
    if (this._actor === null) {
      return;
    }
    this._hidden = !visible;
    this._actor.reactive = visible;
    const target = visible ? SHOWN_OPACITY : HIDDEN_OPACITY;
    if (!this._interfaceSettings.get_boolean('enable-animations')) {
      this._actor.opacity = target;
      return;
    }
    this._actor.ease({
      opacity: target,
      duration: FADE_MS,
      mode: Clutter.AnimationMode.EASE_OUT_QUAD,
    });
  }
}

export default class TreeDockExtension extends Extension {
  enable() {
    this._dock = new TreeDock(this.getSettings());
    this._dock.enable();
  }

  disable() {
    if (this._dock) {
      this._dock.disable();
      this._dock = null;
    }
  }
}
