import Gio from 'gi://Gio';
import GLib from 'gi://GLib';

const DBUS_IFACE = `
<node>
  <interface name="org.guake.JsonPointer">
    <method name="GetPointer">
      <arg type="i" direction="out" name="x"/>
      <arg type="i" direction="out" name="y"/>
    </method>
  </interface>
</node>`;

export default class GuakePointerExtension {
    _dbusId = null;

    enable() {
        const nodeInfo = Gio.DBusNodeInfo.new_for_xml(DBUS_IFACE);

        this._dbusId = Gio.DBus.session.register_object(
            '/org/guake/JsonPointer',
            nodeInfo.interfaces[0],
            (connection, sender, path, ifaceName, methodName, params, invocation) => {
                if (methodName === 'GetPointer') {
                    const tracker = global.backend.get_cursor_tracker();
                    const [coords] = tracker.get_pointer();
                    invocation.return_value(
                        new GLib.Variant('(ii)', [
                            Math.round(coords.x),
                            Math.round(coords.y),
                        ])
                    );
                }
            },
            null,
            null,
        );
    }

    disable() {
        if (this._dbusId) {
            Gio.DBus.session.unregister_object(this._dbusId);
            this._dbusId = null;
        }
    }
}
