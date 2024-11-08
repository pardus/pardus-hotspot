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
    """Initialize network interface for hotspot creation."""
    global device_path, device_proxy, device_iface
    device_path = nm_iface.GetDeviceByIpIface(iface)
    device_proxy = bus.get_object("org.freedesktop.NetworkManager", device_path)
    device_iface = dbus.Interface(device_proxy, "org.freedesktop.NetworkManager.Device")

def create_hotspot(ssid="Hotspot", passwd=None, encrypt=None, band=None):
    """
    Create a Wi-Fi hotspot with parameters.

    Args:
        ssid (str): Network name
        passwd (str): Network password
        encrypt (str): Encryption type (sae/wpa-psk)
        band (str): Frequency band (bg = 2.4GHz, a = 5GHz)
    """
    global current_hotspot_uuid

    # Default to SAE (WPA3) if password exists, otherwise no encryption
    if passwd:
        encrypt = encrypt if encrypt in ["sae", "wpa-psk"] else "sae"
    else:
        print("no password")
        encrypt = "none"

    # Default to 2.4GHz band if not specified or invalid
    band = band if band in ["bg", "a"] else "bg"

    # For 2.4GHz (bg), use channel 1
    # For 5GHz (a), use channel 36
    channel = dbus.UInt32(1 if band == "bg" else 36)

    current_hotspot_uuid = str(uuid.uuid4())

    # Basic connection settings
    connection_settings = dbus.Dictionary({
        "type": "802-11-wireless",
        "uuid": current_hotspot_uuid,
        "id": "hotspot"
    })

    # WiFi settings
    wifi_settings = dbus.Dictionary({
        "ssid": dbus.ByteArray(ssid.encode("utf-8")),
        "mode": "ap",               # Access Point mode
        "band": band,               # Frequency band
        "channel": channel          # Channel for the band
    })

    # Security settings (WPA3/WPA2)
    security_settings = dbus.Dictionary({
        "key-mgmt": encrypt,        # Encryption type
        "pairwise": ["ccmp"],       # AES encryption
        "proto": ["rsn"]            # Modern security protocol
    })

    if passwd:
        security_settings["psk"] = passwd

    # IP settings for connection sharing
    ip4_settings = dbus.Dictionary({"method": "shared"})
    ip6_settings = dbus.Dictionary({"method": "auto"})

    # Combine all settings
    connection = dbus.Dictionary({
        "connection": connection_settings,
        "802-11-wireless": wifi_settings,
        "802-11-wireless-security": security_settings,
        "ipv4": ip4_settings,
        "ipv6": ip6_settings,
    })

    # Remove any existing hotspot before creating new one
    find_and_remove_connection()

    try:
        # Create new connection
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
    except dbus.exceptions.DBusException as e:
        error_msg = str(e).lower()
        # If WPA3 fails, fallback to WPA2
        if "sae" in error_msg and encrypt == "sae":
            return create_hotspot(
                ssid=ssid,
                passwd=passwd,
                encrypt="wpa-psk",
                band=band
            )
        raise
    except Exception as e:
        print(f"Error creating hotspot: {e}")
        raise


def update_hotspot_settings(band, encrypt, ssid="Hotspot", passwd=None):
    """
    Update hotspot settings based on user selection.

    Args:
        band (str): "2.4GHz" or "5GHz"
        encrypt (str): "WPA-PSK" or "SAE"
        ssid (str): Network name
        passwd (str): Network password
    """
    global wifi_settings, security_settings

    # Set the band settings based on user selection
    if band == "2.4GHz":
        wifi_band = "bg"
    elif band == "5GHz":
        wifi_band = "a"
    else:
        wifi_band = "bg"  # Default to 2.4GHz if band is not specified

    if encrypt == "WPA-PSK":
        key_mgmt = "wpa-psk"
    elif encrypt == "SAE":
        key_mgmt = "sae"
    else:
        # If no password, use no encryption
        key_mgmt = "sae" if passwd else "none"

    # Convert strings to ByteArrays for NetworkManager
    ssid_bytes = dbus.ByteArray(ssid.encode("utf-8")) if ssid else b""
    passwd_bytes = dbus.ByteArray(passwd.encode("utf-8")) if passwd else b""

    # WiFi settings
    wifi_settings = {
        "ssid": ssid_bytes,
        "mode": "ap",
        "band": wifi_band,
        "channel": dbus.UInt32(1),
    }

    # Security settings
    security_settings = {
        "key-mgmt": key_mgmt,
        "pairwise": ["ccmp"],
        "proto": ["rsn"],
    }

    if passwd:
        security_settings["psk"] = passwd_bytes


def remove_hotspot():
    """Clean up and remove the active hotspot connection."""
    global device_path, device_proxy, device_iface
    global active_connection_path, active_connection_proxy, active_connection_props

    # First remove the connection
    find_and_remove_connection()

    # Then disconnect device if active
    if device_iface is not None:
        try:
            props = dbus.Interface(device_proxy, "org.freedesktop.DBus.Properties")
            state = props.Get("org.freedesktop.NetworkManager.Device", "State")
            if state == 100:  # NM_DEVICE_STATE_ACTIVATED
                device_iface.Disconnect()
        except dbus.exceptions.DBusException as e:
            if "NotActive" not in str(e):
                print(f"Error disconnecting device: {e}")

    # Reset all connection variables
    active_connection_path = None
    active_connection_proxy = None
    active_connection_props = None

    return True


def find_and_remove_connection(hotspot_uuid=None):
    """
    Find and remove a specific hotspot connection.

    Args:
        hotspot_uuid (str): UUID of connection to remove. Uses current if None.
    """
    if hotspot_uuid is None:
        hotspot_uuid = current_hotspot_uuid

    for path in settings_iface.ListConnections():
        try:
            connection_proxy = bus.get_object("org.freedesktop.NetworkManager", path)
            connection_settings = dbus.Interface(
                connection_proxy, "org.freedesktop.NetworkManager.Settings.Connection"
            ).GetSettings()

            if connection_settings["connection"]["uuid"] == hotspot_uuid:
                dbus.Interface(
                    connection_proxy, "org.freedesktop.NetworkManager.Settings.Connection"
                ).Delete()
                break
        except dbus.exceptions.DBusException:
            continue


def get_connection_state():
    """Get the current state of the network connection."""
    if active_connection_props is None:
        return 0
    return active_connection_props.Get(
        "org.freedesktop.NetworkManager.Connection.Active", "State"
    )


def is_connection_activated():
    """Check if hotspot is successfully activated, added for DEBUGGING"""
    return get_connection_state() == 2  # NM_ACTIVE_CONNECTION_STATE_ACTIVATED


def is_wifi_enabled():
    """Check if WiFi hardware is enabled and available."""
    nm_props = dbus.Interface(nm_proxy, "org.freedesktop.DBus.Properties")
    return nm_props.Get("org.freedesktop.NetworkManager", "WirelessEnabled")
