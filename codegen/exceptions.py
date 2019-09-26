from dbus.exceptions import DBusException


class UnknownInterface(DBusException):
    "Raised when a dbus interface does not implement the interface expected"

    def __init__(self, this, that):
        super().__init__(
            "com.example.UnknownInterface",
            "%s does not implement the interface %s" % (this, that),
        )


class UnknownProperty(DBusException):
    "Raised when a dbus interface does not possess the property expected"

    def __init__(self, iface, prop, rw=None):
        access = (" %sable" % rw[:4]) if rw else ""  # read/write/whatever

        super().__init__(
            "com.example.UnknownProperty",
            '%s has no%s property "%s"' % (iface, access, prop),
        )
