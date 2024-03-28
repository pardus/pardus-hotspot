import dbus

import uuid


# Initialize D-Bus system bus
bus = dbus.SystemBus()

# Get NetworkManager settings and interface objects
settings_proxy = bus.get_object(
    "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager/Settings"
)
settings_iface = dbus.Interface(
    settings_proxy, "org.freedesktop.NetworkManager.Settings"
)

nm_proxy = bus.get_object(
    "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
)
nm_iface = dbus.Interface(nm_proxy, "org.freedesktop.NetworkManager")

# Initialize variables
device_path = None
device_proxy = None
device_iface = None
active_connection_path = None
active_connection_proxy = None
active_connection_props = None
current_hotspot_uuid = None


def set_network_interface(iface):
    """
    Set the network interface for the script to operate on.
    """
    global device_path, device_proxy, device_iface
    device_path = nm_iface.GetDeviceByIpIface(iface)
    device_proxy = bus.get_object("org.freedesktop.NetworkManager", device_path)
    device_iface = dbus.Interface(device_proxy, "org.freedesktop.NetworkManager.Device")


def create_hotspot(ssid="Hotspot", passwd=None):
    """
    Create a Wi-Fi hotspot with the specified SSID and optional password.
    """
    global current_hotspot_uuid
    # Create an unique uuid for hotspot
    current_hotspot_uuid = str(uuid.uuid4())

    connection_settings = dbus.Dictionary(
        {"type": "802-11-wireless", "uuid": current_hotspot_uuid, "id": "hotspot"}
    )

    wifi_settings = dbus.Dictionary(
        {
            "ssid": dbus.ByteArray(ssid.encode("utf-8")),
            "mode": "ap",
            "band": "bg",
            "channel": dbus.UInt32(1),
        }
    )

    security_settings = dbus.Dictionary(
        {"key-mgmt": "sae",
         "psk": passwd,
         "pairwise": ["ccmp"],
         "proto": ["rsn"]}
    )

    ip4_settings = dbus.Dictionary({"method": "shared"})
    ip6_settings = dbus.Dictionary({"method": "auto"})

    connection = dbus.Dictionary(
        {
            "connection": connection_settings,
            "802-11-wireless": wifi_settings,
            "802-11-wireless-security": security_settings,
            "ipv4": ip4_settings,
            "ipv6": ip6_settings,
        }
    )

    # Remove existing hotspot connection
    find_and_remove_connection()

    # Add a new connection
    connection_path = settings_iface.AddConnection(connection)

    # Activate the connection
    global active_connection_path, active_connection_proxy, active_connection_props
    active_connection_path = nm_iface.ActivateConnection(
        connection_path, device_path, "/"
    )
    active_connection_proxy = bus.get_object(
        "org.freedesktop.NetworkManager", active_connection_path
    )
    active_connection_props = dbus.Interface(
        active_connection_proxy, "org.freedesktop.DBus.Properties"
    )


def get_connection_state():
    """
    Get the state of the active network connection.
    """
    if active_connection_props is None:
        return 0
    state = active_connection_props.Get(
        "org.freedesktop.NetworkManager.Connection.Active", "State"
    )
    return state


def is_connection_activated():
    """
    Check if the network connection is in the "activated" state.
    """
    return get_connection_state() == 2  # NM_ACTIVE_CONNECTION_STATE_ACTIVATED


def is_wifi_enabled():
    """
    Check if the Wi-Fi hardware is physically enabled.
    """
    nm_props = dbus.Interface(nm_proxy, "org.freedesktop.DBus.Properties")

    # Check the WirelessEnabled property
    wifi_enabled = nm_props.Get("org.freedesktop.NetworkManager", "WirelessEnabled")
    return wifi_enabled


def update_hotspot_settings(band, encrypt, ssid="Hotspot", passwd=None):
    """
    Update hotspot settings based on user selection.
    """
    global wifi_settings, security_settings

    # Set the band settings based on user selection
    if band == "2.4GHz":
        wifi_band = "bg"
    elif band == "5GHz":
        wifi_band = "a"
    else:
        wifi_band = "bg"  # Default to 2.4GHz if band is not specified

    # Set the encryption settings based on user selection
    if encrypt == "WPA-PSK":
        key_mgmt = "wpa-psk"
    elif encrypt == "SAE":
        key_mgmt = "sae"
    elif encrypt == "None":
        key_mgmt = "none"
    else:
        # Handle unsupported encryption methods
        print("Unsupported encryption method:", encrypt)
        key_mgmt = "none"  # Default to no encryption if not supported

    ssid_bytes = dbus.ByteArray(ssid.encode("utf-8")) if ssid is not None else b""
    passwd_bytes = dbus.ByteArray(passwd.encode("utf-8")) if passwd is not None else b""

    wifi_settings = {
        "ssid": ssid_bytes,
        "mode": "ap",
        "band": wifi_band,
        "channel": dbus.UInt32(1),
    }

    security_settings = {
        "key-mgmt": key_mgmt,
        "pairwise": ["ccmp"],
        "proto": ["rsn"],
    }

    # Check if encryption method requires a password
    if key_mgmt not in ["none", "ieee8021x"] and not passwd:
        print("Password is required for encryption. Defaulting to no encryption.")
        security_settings["key-mgmt"] = "none"
    else:
        security_settings["psk"] = passwd_bytes


def update_hotspot_settings_helper(band, encrypt, ssid="Hotspot", passwd=None):
    """
    Helper function to update hotspot settings based on user selection.
    """
    global current_hotspot_uuid

    # Set the band settings based on user selection
    if band == "2.4GHz":
        wifi_band = "bg"
    elif band == "5GHz":
        wifi_band = "a"
    else:
        wifi_band = "bg"  # Default to 2.4GHz if band is not specified

    # Set the encryption settings based on user selection
    if encrypt == "WPA-PSK":
        key_mgmt = "wpa-psk"
    elif encrypt == "SAE":
        key_mgmt = "sae"
    elif encrypt == "None":
        key_mgmt = "none"
    else:
        # Handle unsupported encryption methods
        print("Unsupported encryption method:", encrypt)
        key_mgmt = "none"  # Default to no encryption if not supported

    ssid_bytes = dbus.ByteArray(ssid.encode("utf-8")) if ssid is not None else b""
    passwd_bytes = dbus.ByteArray(passwd.encode("utf-8")) if passwd is not None else b""

    wifi_settings = {
        "ssid": ssid_bytes,
        "mode": "ap",
        "band": wifi_band,
        "channel": dbus.UInt32(1),
    }

    security_settings = {
        "key-mgmt": key_mgmt,
        "psk": passwd_bytes,
        "pairwise": ["ccmp"],
        "proto": ["rsn"],
    }

    ip4_settings = {"method": "shared"}
    ip6_settings = {"method": "auto"}

    connection_settings = {
        "type": "802-11-wireless", "uuid": current_hotspot_uuid, "id": "hotspot"
    }

    connection = {
        "connection": connection_settings,
        "802-11-wireless": wifi_settings,
        "802-11-wireless-security": security_settings,
        "ipv4": ip4_settings,
        "ipv6": ip6_settings,
    }

    return connection


def find_and_remove_connection(hotspot_uuid=None):
    """
    Find an existing hotspot connection and remove it.
    """
    global current_hotspot_uuid

    if hotspot_uuid is None:
        hotspot_uuid = current_hotspot_uuid

    for path in settings_iface.ListConnections():
        connection_proxy = bus.get_object("org.freedesktop.NetworkManager", path)
        connection_settings = dbus.Interface(
            connection_proxy, "org.freedesktop.NetworkManager.Settings.Connection"
        ).GetSettings()

        if connection_settings["connection"]["uuid"] == hotspot_uuid:
            dbus.Interface(
                connection_proxy, "org.freedesktop.NetworkManager.Settings.Connection"
            ).Delete()

            break


def remove_hotspot():
    """
    Disconnect from the hotspot and remove the connection.
    """
    global device_path, device_proxy, device_iface
    global active_connection_path, active_connection_proxy, active_connection_props

    # Check if the device interface is initialized
    if device_iface is None:
        # print("No network device interface found.")
        return False

    # Attempt to disconnect
    try:
        device_iface.Disconnect()
    except Exception as e:
        print(f"Error disconnecting the device: {e}")

    find_and_remove_connection()

    # Reset variables
    active_connection_path = None
    active_connection_proxy = None
    active_connection_props = None

    return True


def find_and_remove_all_hotspot_connections():
    """
    Do not use this function - only for test -
    """
    global settings_iface

    connection_paths = settings_iface.ListConnections()
    for path in connection_paths:
        connection_proxy = bus.get_object("org.freedesktop.NetworkManager", path)
        connection_settings = dbus.Interface(
            connection_proxy, dbus_interface="org.freedesktop.NetworkManager.Settings.Connection"
        )
        settings = connection_settings.GetSettings()

        if settings.get('802-11-wireless', {}).get('mode') == 'ap':
            print(f"Hotspot connection found and being removed: {settings.get('connection', {}).get('id')}")
            connection_settings.Delete()
