/* extension.js
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

/* exported init */
const {
    Gio,
} = imports.gi;

const MR_DBUS_IFACE = `
<node>
   <interface name="org.gnome.Shell.Extensions.AutoKey">
      <method name="List">
         <arg type="s" direction="out" name="win" />
      </method>
      <method name="Details">
         <arg type="u" direction="in" name="winid" />
         <arg type="s" direction="out" name="win" />
      </method>
      <method name="GetTitle">
         <arg type="u" direction="in" name="winid" />
         <arg type="s" direction="out" name="win" />
      </method>
      <method name="MoveToWorkspace">
         <arg type="u" direction="in" name="winid" />
         <arg type="u" direction="in" name="workspaceNum" />
      </method>
      <method name="MoveResize">
         <arg type="u" direction="in" name="winid" />
         <arg type="i" direction="in" name="x" />
         <arg type="i" direction="in" name="y" />
         <arg type="u" direction="in" name="width" />
         <arg type="u" direction="in" name="height" />
      </method>
      <method name="Resize">
         <arg type="u" direction="in" name="winid" />
         <arg type="u" direction="in" name="width" />
         <arg type="u" direction="in" name="height" />
      </method>
      <method name="Move">
         <arg type="u" direction="in" name="winid" />
         <arg type="i" direction="in" name="x" />
         <arg type="i" direction="in" name="y" />
      </method>
      <method name="Maximize">
         <arg type="u" direction="in" name="winid" />
      </method>
      <method name="Minimize">
         <arg type="u" direction="in" name="winid" />
      </method>
      <method name="Unmaximize">
         <arg type="u" direction="in" name="winid" />
      </method>
      <method name="Unminimize">
         <arg type="u" direction="in" name="winid" />
      </method>
      <method name="Activate">
         <arg type="u" direction="in" name="winid" />
      </method>
      <method name="Close">
         <arg type="u" direction="in" name="winid" />
      </method>
      <method name="GetMouseLocation">
            <arg type="i" direction="out" name="x" />
            <arg type="i" direction="out" name="y" />
      </method>
      <method name="ScreenSize">
            <arg type="i" direction="out" name="width" />
            <arg type="i" direction="out" name="height" />
      </method>
      <method name="CheckVersion">
            <arg type="s" direction="out" name="version" />
      </method>
   </interface>
</node>`;


class Extension {
    enable() {
        this._dbus = Gio.DBusExportedObject.wrapJSObject(MR_DBUS_IFACE, this);
        this._dbus.export(Gio.DBus.session, '/org/gnome/Shell/Extensions/AutoKey');
    }

    disable() {
        this._dbus.flush();
        this._dbus.unexport();
        delete this._dbus;
    }

    _get_window_by_wid(winid) {
        let win = global.get_window_actors().find(w => w.meta_window.get_id() == winid);
        return win;
    }

    List() {
        let win = global.get_window_actors();

        let workspaceManager = global.workspace_manager;

        var winJsonArr = [];
        win.forEach(function (w) {
            winJsonArr.push({
                wm_class: w.meta_window.get_wm_class(),
                wm_class_instance: w.meta_window.get_wm_class_instance(),
                wm_title: w.meta_window.get_title(),
                workspace: w.meta_window.get_workspace().index(),
                desktop: w.meta_window.get_monitor(),
                pid: w.meta_window.get_pid(),
                id: w.meta_window.get_id(),
                frame_type: w.meta_window.get_frame_type(),
                window_type: w.meta_window.get_window_type(),
                width: w.get_width(),
                height: w.get_height(),
                x: w.get_x(),
                y: w.get_y(),
                focus: w.meta_window.has_focus(),
                in_current_workspace: w.meta_window.located_on_workspace(workspaceManager.get_active_workspace()),
            });
        });
        return JSON.stringify(winJsonArr);
    }

    Details(winid) {
        let w = this._get_window_by_wid(winid);
        let workspaceManager = global.workspace_manager;
        let currentmonitor = global.display.get_current_monitor();
        // let monitor = global.display.get_monitor_geometry(currentmonitor);
        if (w) {
            return JSON.stringify({
                wm_class: w.meta_window.get_wm_class(),
                wm_class_instance: w.meta_window.get_wm_class_instance(),
                pid: w.meta_window.get_pid(),
                id: w.meta_window.get_id(),
                width: w.get_width(),
                height: w.get_height(),
                x: w.get_x(),
                y: w.get_y(),
                focus: w.meta_window.has_focus(),
                in_current_workspace: w.meta_window.located_on_workspace(workspaceManager.get_active_workspace()),
                moveable: w.meta_window.allows_move(),
                resizeable: w.meta_window.allows_resize(),
                canclose: w.meta_window.can_close(),
                canmaximize: w.meta_window.can_maximize(),
                maximized: w.meta_window.get_maximized(),
                canminimize: w.meta_window.can_minimize(),
                canshade: w.meta_window.can_shade(),
                display: w.meta_window.get_display(),
                frame_bounds: w.meta_window.get_frame_bounds(),
                frame_type: w.meta_window.get_frame_type(),
                window_type: w.meta_window.get_window_type(),
                layer: w.meta_window.get_layer(),
                monitor: w.meta_window.get_monitor(),
                role: w.meta_window.get_role(),
                area: w.meta_window.get_work_area_current_monitor(),
                area_all: w.meta_window.get_work_area_all_monitors(),
                area_cust: w.meta_window.get_work_area_for_monitor(currentmonitor),
            });
        } else {
            throw new Error('Not found');
        }
    }

    GetTitle(winid) {
        let w = this._get_window_by_wid(winid);
        if (w)
            return w.meta_window.get_title();
        else
            throw new Error('Not found');
    }

    MoveToWorkspace(winid, workspaceNum) {
        let win = this._get_window_by_wid(winid).meta_window;
        if (win)
            win.change_workspace_by_index(workspaceNum, false);
        else
            throw new Error('Not found');
    }

    MoveResize(winid, x, y, width, height) {
        let win = this._get_window_by_wid(winid);

        if (win) {
            if (win.meta_window.maximized_horizontally || win.meta_window.maximized_vertically)
                win.meta_window.unmaximize(3);


            win.meta_window.move_resize_frame(1, x, y, width, height);
        } else {
            throw new Error('Not found');
        }
    }

    Resize(winid, width, height) {
        let win = this._get_window_by_wid(winid);
        if (win) {
            if (win.meta_window.maximized_horizontally || win.meta_window.maximized_vertically)
                win.meta_window.unmaximize(3);

            win.meta_window.move_xCoordresize_frame(1, win.get_x(), win.get_y(), width, height);
        } else {
            throw new Error('Not found');
        }
    }

    Move(winid, x, y) {
        let win = this._get_window_by_wid(winid);
        if (win) {
            if (win.meta_window.maximized_horizontally || win.meta_window.maximized_vertically)
                win.meta_window.unmaximize(3);

            win.meta_window.move_frame(1, x, y);
        } else {
            throw new Error('Not found');
        }
    }

    Maximize(winid) {
        let win = this._get_window_by_wid(winid).meta_window;
        if (win)
            win.maximize(3);
        else
            throw new Error('Not found');
    }

    Minimize(winid) {
        let win = this._get_window_by_wid(winid).meta_window;
        if (win)
            win.minimize();
        else
            throw new Error('Not found');
    }

    Unmaximize(winid) {
        let win = this._get_window_by_wid(winid).meta_window;
        if (win)
            win.unmaximize(3);
        else
            throw new Error('Not found');
    }

    Unminimize(winid) {
        let win = this._get_window_by_wid(winid).meta_window;
        if (win)
            win.unminimize();
        else
            throw new Error('Not found');
    }

    Activate(winid) {
        let win = this._get_window_by_wid(winid).meta_window;
        if (win)
            win.activate(0);
        else
            throw new Error('Not found');
    }

    Close(winid) {
        let win = this._get_window_by_wid(winid).meta_window;
        if (win)
            win.kill();
            // win.delete(Math.floor(Date.now() / 1000));
        else
            throw new Error('Not found');
    }

    GetMouseLocation() {
        let [x, y, mask] = global.get_pointer();
        return [x, y];
    }

    ScreenSize() {
        let x = global.screen_width;
        let y = global.screen_height;
        return [x, y];
    }

    CheckVersion() {
        return '0.1';
    }
}

/**
 *
 */
function init() {
    // called by gnome shell when extension is loaded
    return new Extension();
}
