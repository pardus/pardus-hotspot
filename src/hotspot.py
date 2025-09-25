import dbus
import uuid
import time
import os
import subprocess
import functools
import dbus.exceptions


def _retry_on_dbus_error(func):
    """
    Retry decorator for Dbus connection errors
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except dbus.exceptions.DBusException as e:
            # Retry for temporary DBus errors
            temporary_errors = [
                "org.freedesktop.DBus.Error.ServiceUnknown",
                "org.freedesktop.DBus.Error.NoReply"
            ]
            if any(err in str(e) for err in temporary_errors):
                print(f"[Retry] Temporary DBus issue in {func.__name__} ..")
                time.sleep(0.5)
                return func(*args, **kwargs)
            raise
    return wrapper


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
nm_props = dbus.Interface(nm_proxy, "org.freedesktop.DBus.Properties")

# Initialize variables
device_path = None
device_proxy = None
device_iface = None
active_connection_path = None
active_connection_proxy = None
active_connection_props = None
current_hotspot_uuid = None


@_retry_on_dbus_error
def disconnect_wifi_connections():
    """Disconnect from all active WiFi connections before creating hotspot."""
    try:
        has_active_wifi = False
        # Get all network devices
        devices = nm_iface.GetAllDevices()

        for device in devices:
            dev_proxy = bus.get_object("org.freedesktop.NetworkManager", device)
            dev_props = dbus.Interface(dev_proxy, "org.freedesktop.DBus.Properties")

            # Check if this is a WiFi device (DT 2 is WiFi)
            if dev_props.Get("org.freedesktop.NetworkManager.Device", "DeviceType") != 2:
                continue

            # Get active connection if any
            active_connection = dev_props.Get("org.freedesktop.NetworkManager.Device", "ActiveConnection")
            if active_connection != "/":
                dev_iface = dbus.Interface(dev_proxy, "org.freedesktop.NetworkManager.Device")
                has_active_wifi = True
                dev_iface.Disconnect()

        if has_active_wifi:
            time.sleep(1)

        return True
    except Exception as e:
        print(f"Error disconnecting WiFi: {e}")
        return False


@_retry_on_dbus_error
def get_hotspot_connection():
    """Internal helper function to get active hotspot connection."""
    try:
        active_connections = nm_props.Get("org.freedesktop.NetworkManager", "ActiveConnections")

        for active_conn_path in active_connections:
            active_conn_proxy = bus.get_object("org.freedesktop.NetworkManager", active_conn_path)
            active_conn_props = dbus.Interface(active_conn_proxy, "org.freedesktop.DBus.Properties")

            connection_path = active_conn_props.Get("org.freedesktop.NetworkManager.Connection.Active", "Connection")
            connection_proxy = bus.get_object("org.freedesktop.NetworkManager", connection_path)
            connection_iface = dbus.Interface(connection_proxy, "org.freedesktop.NetworkManager.Settings.Connection")

            settings = connection_iface.GetSettings()

            if settings["connection"]["type"] == "802-11-wireless" and settings["802-11-wireless"]["mode"] == "ap":
                return active_conn_path, connection_path, connection_iface, settings

        return None, None, None, None
    except Exception as e:
        print(f"Error getting active hotspot: {e}")
        return None, None, None, None


@_retry_on_dbus_error
def get_active_hotspot_info():
    """Return SSID, password, and encryption type of the active hotspot"""
    _, _, connection_iface, settings = get_hotspot_connection()

    if not settings:
        return None

    ssid_bytes = settings["802-11-wireless"]["ssid"]
    ssid = "".join([chr(b) for b in ssid_bytes])
    password = ""
    encryption = ""

    if "802-11-wireless-security" in settings:
        wireless_security = settings.get("802-11-wireless-security", {})

        try:
            secrets = connection_iface.GetSecrets("802-11-wireless-security")
            if "802-11-wireless-security" in secrets:
                wireless_security.update(secrets["802-11-wireless-security"])
        except dbus.DBusException as e:
            print(f"Error retrieving secrets: {e}")

        password = wireless_security.get("psk", "")
        encryption = wireless_security.get("key-mgmt", "")
    else:
        encryption = "none"

    return {
        "ssid": ssid,
        "password": password,
        "encryption": encryption
    }


@_retry_on_dbus_error
def disable_connection():
    """
    Disable active hotspot connection if exists.
    Returns True if successfully disabled
    """
    active_conn_path, _, _, _ = get_hotspot_connection()
    if active_conn_path:
        try:
            nm_iface.DeactivateConnection(active_conn_path)
            return True
        except Exception as e:
            print(f"Error disabling connection: {e}")

    return False

@_retry_on_dbus_error
def set_network_interface(iface):
    """Initialize network interface for hotspot creation."""
    global device_path, device_proxy, device_iface
    device_path = nm_iface.GetDeviceByIpIface(iface)
    device_proxy = bus.get_object("org.freedesktop.NetworkManager", device_path)
    device_iface = dbus.Interface(device_proxy, "org.freedesktop.NetworkManager.Device")


def check_ip_forwarding():
    """
    Check if system needs IP forwarding fix
    Returns True if Docker is installed or IP forwarding is disabled
    """
    # Check if Docker is installed
    docker_exists = os.path.exists('/var/run/docker.sock')

    # Check IP forwarding status
    with open('/proc/sys/net/ipv4/ip_forward', 'r') as f:
        forwarding_disabled = f.read().strip() != '1'

    return docker_exists or forwarding_disabled


def create_hotspot(ssid="Hotspot", passwd=None, encrypt=None, band=None, forward=False):
    """
    Create a Wi-Fi hotspot with parameters.

    Args:
        ssid (str): Network name
        passwd (str): Network password
        encrypt (str): Encryption type (sae/wpa-psk)
        band (str): Frequency band (bg = 2.4GHz, a = 5GHz)
    """
    global current_hotspot_uuid

    disconnect_wifi_connections()

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
        "id": "pardus-hotspot",
        "autoconnect": dbus.Boolean(False)
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
    remove_hotspot()

    try:
        # Create new connection
        connection_path = settings_iface.AddConnection(connection)

        # Activate the connection
        global active_connection_path, active_connection_proxy, active_connection_props
        active_connection_path = nm_iface.ActivateConnection(
            connection_path, device_path, "/"
        )

        # For docker - ip forwarding control
        if check_ip_forwarding() or forward:
            actions_path = os.path.dirname(os.path.abspath(__file__)) + "/Actions.py"
            try:
                command = ["/usr/bin/pkexec", actions_path, "forward"]
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to configure IP forwarding: {e}")

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

    # First disable any active connection
    disable_connection()

    if settings_iface:
        remove_all_hotspot_connections()

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

@_retry_on_dbus_error
def remove_all_hotspot_connections():
    """Delete old hotspot profiles."""
    try:
        connection_paths = settings_iface.ListConnections()
    except dbus.DBusException as e:
        print(f"DBus error while listing connections: {e}")
        return

    for path in connection_paths:
        try:
            connection_proxy = bus.get_object("org.freedesktop.NetworkManager", path)
            connection_iface = dbus.Interface(
                connection_proxy, "org.freedesktop.NetworkManager.Settings.Connection"
            )
            settings = connection_iface.GetSettings()

            if settings.get("connection", {}).get("type") == "802-11-wireless":
                wifi_settings = settings.get("802-11-wireless", {})
                if (wifi_settings.get("mode") == "ap" and
                    settings.get("connection", {}).get("id") == "pardus-hotspot"):
                    connection_iface.Delete()
        except dbus.DBusException as e:
            print(f"Failed to delete connection {path}: {e}")
            continue

@_retry_on_dbus_error
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


@_retry_on_dbus_error
def is_wifi_enabled():
    """Check if WiFi hardware is enabled and available."""
    try:
        bus = dbus.SystemBus()
        nm_proxy = bus.get_object("org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager")
        nm_props = dbus.Interface(nm_proxy, "org.freedesktop.DBus.Properties")
        return nm_props.Get("org.freedesktop.NetworkManager", "WirelessEnabled")
    except dbus.exceptions.DBusException as e:
        print(f"[DBus] Wi-Fi check failed: {e}")
        return False
