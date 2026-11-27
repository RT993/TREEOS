// TREE dock: a GNOME Shell 46 extension showing pinned and running applications.
// See docs/specifications/dock.md for the behaviour this file implements.

import Clutter from 'gi://Clutter';
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

const ICON_SIZE = 48;
const INDICATOR_SIZE = 5;
const UNAVAILABLE_OPACITY = 102; // 40% of 255
const PINNED_KEY = 'pinned-apps';
const BOTTOM_MARGIN = 8;
const FALLBACK_ICON = 'application-x-executable';
const TOOLTIP_GAP = 6;

class TreeDock {
  constructor(settings) {
    this._settings = settings;
    this._appSystem = Shell.AppSystem.get_default();
    this._signalIds = [];
    this._actor = null;
    this._menu = null;
    this._menuManager = null;
    this._tooltip = null;
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

    this._connect(this._settings, `changed::${PINNED_KEY}`, () => this.rebuild());
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

    this._closeMenu();
    this._hideTooltip();
    if (this._actor !== null) {
      Main.layoutManager.removeChrome(this._actor);
      this._actor.destroy();
      this._actor = null;
    }
  }

  rebuild() {
    if (this._actor === null) {
      return;
    }
    this._closeMenu();
    this._hideTooltip();
    this._actor.destroy_all_children();

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
    for (const app of running) {
      this._actor.add_child(this._buildItem(app.get_id(), false));
    }

    this._reposition();
  }

  _connect(object, signal, callback) {
    this._signalIds.push([object, object.connect(signal, callback)]);
  }

  _buildItem(id, pinned) {
    const app = this._appSystem.lookup_app(id);
    const name = app !== null ? app.get_name() : id;

    const icon = app !== null
      ? app.create_icon_texture(ICON_SIZE)
      : new St.Icon({icon_name: FALLBACK_ICON, icon_size: ICON_SIZE});

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
    const x = monitor.x + Math.floor((monitor.width - width) / 2);
    const y = monitor.y + monitor.height - height - BOTTOM_MARGIN;
    this._actor.set_position(x, y);
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
