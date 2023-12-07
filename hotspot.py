import dbus, sys, time

our_uuid = "2b0d0f1d-b79d-43af-bde1-71744625642e"


bus = dbus.SystemBus()

proxy_settings = bus.get_object(
    "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/Settings"
)
settings = dbus.Interface(proxy_settings, "org.freedesktop.NetworkManager.Settings")

proxy_nm = bus.get_object(
    "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
)
nm = dbus.Interface(proxy_nm, "org.freedesktop.NetworkManager")


devpath = None
proxy_device = None
device = None
acpath = None
proxy_prop = None
active_props = None

def set_iface(iface):
    global devpath
    global proxy_device
    global device
    devpath = nm.GetDeviceByIpIface(iface)
    proxy_device = bus.get_object("org.freedesktop.NetworkManager", devpath)
    device = dbus.Interface(proxy_device, "org.freedesktop.NetworkManager.Device")


def create_hotspot(ssid="Hotspot",passwd=None):
    s_con = dbus.Dictionary(
        {"type": "802-11-wireless", "uuid": our_uuid, "id": "hotspot"}
    )

    s_wifi = dbus.Dictionary(
        {
            "ssid": dbus.ByteArray(ssid.encode("utf-8")), # Connection Name
            "mode": "ap", # Network Mode
            "band": "bg", # Band Selection
            "channel": dbus.UInt32(1),
        }
    )
    if passwd:
        s_wsec = dbus.Dictionary({"key-mgmt": "wpa-psk", "psk": passwd}) # Encryption Method
    else:
        s_wsec = dbus.Dictionary({"key-mgmt": "none"})
    s_ip4 = dbus.Dictionary({"method": "shared"})
    s_ip6 = dbus.Dictionary({"method": "ignore"})

    con = dbus.Dictionary(
        {
            "connection": s_con,
            "802-11-wireless": s_wifi,
            "802-11-wireless-security": s_wsec,
            "ipv4": s_ip4,
            "ipv6": s_ip6,
        }
    )

    find_remove_connection()

    # Add new connection
    connection_path = settings.AddConnection(con)

    # define props
    global acpath
    global proxy_prop
    global active_props
    acpath = nm.ActivateConnection(connection_path, devpath, "/")
    proxy_prop = bus.get_object("org.freedesktop.NetworkManager", acpath)
    active_props = dbus.Interface(proxy_prop, "org.freedesktop.DBus.Properties")

def get_state():
    if active_props == None:
        return 0
    state = active_props.Get("org.freedesktop.NetworkManager.Connection.Active", "State")
    return state

def prop_connection():
    return get_state() == 2 # NM_ACTIVE_CONNECTION_STATE_ACTIVATED

def find_remove_connection():
    # Find existing hotspot connection and remove
    for path in settings.ListConnections():
        proxy_con = bus.get_object("org.freedesktop.NetworkManager", path)
        settings_connection = dbus.Interface(
            proxy_con, "org.freedesktop.NetworkManager.Settings.Connection"
        )
        config = settings_connection.GetSettings()
        if config["connection"]["uuid"] == our_uuid:
            config = settings_connection.GetSettings()
            settings_connection.Delete()
            break

def remove_hotspot():
    global acpath
    global proxy_prop
    global active_props
    device.Disconnect()
    find_remove_connection()

    acpath = None
    proxy_prop = None
    active_props = None
    return True

