def toggle_guake_by_dbus():
    import dbus

    try:
        bus = dbus.SessionBus()
        remote_object = bus.get_object('org.guake3.RemoteControl', '/org/guake3/RemoteControl')
        print("Sending 'toggle' message to Guake3")
        remote_object.show_hide()
    except dbus.DBusException:
        pass
