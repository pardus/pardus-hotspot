import dbus
import dbus.exceptions
import uuid
import time
import os
import grp
import pwd
import subprocess
from logging_config import get_logger

logger = get_logger()


# Recoverable DBus errors
RECOVERABLE_DBUS_ERRORS = [
    "org.freedesktop.DBus.Error.ServiceUnknown",
    "org.freedesktop.DBus.Error.NoReply",
    "org.freedesktop.DBus.Error.Disconnected",
    "org.freedesktop.DBus.Error.NameHasNoOwner"
]

# DBus connection state
_bus = None
_settings_iface = None
_nm_iface = None
_nm_props = None

# Device and connection state
device_path = None
device_proxy = None
device_iface = None
active_connection_path = None
active_connection_proxy = None
active_connection_props = None
current_hotspot_uuid = None
forwarding_configured = False


def _is_recoverable_error(e):
    error_str = str(e)
    return any(err in error_str for err in RECOVERABLE_DBUS_ERRORS)


def _reset_connection():
    """Reset all DBus connections for reconnection"""
    global _bus, _settings_iface, _nm_iface, _nm_props
    global device_path, device_proxy, device_iface
    global active_connection_proxy, active_connection_props

    if _bus is not None:
        try:
            _bus.close()
        except Exception:
            pass

    _bus = None
    _settings_iface = None
    _nm_iface = None
    _nm_props = None
    device_path = None
    device_proxy = None
    device_iface = None
    active_connection_proxy = None
    active_connection_props = None


def check_user_network_permissions():
    """
    Check whether current user is in netdev group
    """
    try:
        if os.geteuid() == 0:
            return True, "yes"

        group_ids = set(os.getgroups())
        group_ids.add(os.getgid())
        group_ids.add(os.getegid())
        group_names = {grp.getgrgid(gid).gr_name for gid in group_ids}

        if "netdev" not in group_names:
            logger.info("User is not in netdev group")
            return False, "no"

        return True, "yes"
    except Exception as e:
        logger.debug(f"Permission pre-check failed, allowing attempt: {e}")
        return True, "unknown"


def _get_bus():
    """Get or create Dbus connection"""
    global _bus

    if _bus is None:
        _bus = dbus.SystemBus(private=True)

    return _bus


def _get_settings_iface():
    """Get nm settings interface"""
    global _settings_iface

    if _settings_iface is None:
        bus = _get_bus()
        settings_proxy = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager/Settings"
        )
        _settings_iface = dbus.Interface(
            settings_proxy,
            "org.freedesktop.NetworkManager.Settings"
        )

    return _settings_iface


def _get_nm_iface():
    """Get nm interface"""
    global _nm_iface

    if _nm_iface is None:
        bus = _get_bus()
        nm_proxy = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager"
        )
        _nm_iface = dbus.Interface(nm_proxy, "org.freedesktop.NetworkManager")

    return _nm_iface


def _get_nm_props():
    """Get nm properties interface"""
    global _nm_props

    if _nm_props is None:
        bus = _get_bus()
        nm_proxy = bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager"
        )
        _nm_props = dbus.Interface(nm_proxy, "org.freedesktop.DBus.Properties")

    return _nm_props


def disconnect_wifi_connections():
    """Disconnect from all active WiFi connections before creating hotspot."""
    try:
        bus = _get_bus()
        nm_iface = _get_nm_iface()
        has_active_wifi = False

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
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        logger.error("Failed to disconnect WiFi connections")
        logger.debug(f"Error details: {e}")
        return False
    except Exception as e:
        logger.error("Failed to disconnect WiFi connections")
        logger.debug(f"Error details: {e}")
        return False


def get_hotspot_connection():
    """Internal helper function to get active hotspot connection."""
    try:
        bus = _get_bus()
        nm_props = _get_nm_props()

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
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        logger.error("Failed to get active hotspot information")
        logger.debug(f"Error details: {e}")
        return None, None, None, None
    except Exception as e:
        logger.error("Failed to get active hotspot information")
        logger.debug(f"Error details: {e}")
        return None, None, None, None


def get_active_hotspot_info():
    """Return SSID, password, and encryption type of the active hotspot"""
    _, _, connection_iface, settings = get_hotspot_connection()

    if not settings:
        return None

    try:
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
            except dbus.exceptions.DBusException as e:
                if _is_recoverable_error(e):
                    logger.info("DBus connection lost, will reconnect on next call")
                    _reset_connection()
                logger.warning("Failed to retrieve connection secrets")
                logger.debug(f"DBus error details: {e}")

            password = wireless_security.get("psk", "")
            encryption = wireless_security.get("key-mgmt", "")
        else:
            encryption = "none"

        return {
            "ssid": ssid,
            "password": password,
            "encryption": encryption
        }
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        logger.error("Failed to get hotspot info")
        logger.debug(f"Error details: {e}")
        return None


def disable_connection():
    """
    Disable active hotspot connection if exists.
    Returns True if successfully disabled.
    """
    active_conn_path, _, _, _ = get_hotspot_connection()
    if active_conn_path:
        try:
            nm_iface = _get_nm_iface()
            nm_iface.DeactivateConnection(active_conn_path)
            return True
        except dbus.exceptions.DBusException as e:
            if _is_recoverable_error(e):
                logger.info("DBus connection lost, will reconnect on next call")
                _reset_connection()
            logger.error("Failed to disable hotspot connection")
            logger.debug(f"Error details: {e}")
        except Exception as e:
            logger.error("Failed to disable hotspot connection")
            logger.debug(f"Error details: {e}")

    return False


def set_network_interface(iface):
    """Initialize network interface for hotspot creation."""
    global device_path, device_proxy, device_iface

    try:
        bus = _get_bus()
        nm_iface = _get_nm_iface()

        device_path = nm_iface.GetDeviceByIpIface(iface)
        device_proxy = bus.get_object("org.freedesktop.NetworkManager", device_path)
        device_iface = dbus.Interface(device_proxy, "org.freedesktop.NetworkManager.Device")
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        logger.error("Failed to set network interface")
        logger.debug(f"Error details: {e}")
        raise


def check_ip_forwarding():
    """
    Check if system needs IP forwarding fix.
    Returns True if IP forwarding is disabled (needs fix)
    """
    try:
        with open('/proc/sys/net/ipv4/ip_forward', 'r') as f:
            return f.read().strip() != '1'
    except (OSError, IOError):
        return True


def create_hotspot(ssid="Hotspot", passwd=None, encrypt=None, band=None, forward=False):
    """
    Create a Wi-Fi hotspot with parameters.

    Args:
        ssid (str): Network name
        passwd (str): Network password
        encrypt (str): Encryption type (sae/wpa-psk)
        band (str): Frequency band (bg = 2.4GHz, a = 5GHz)
        forward (bool): Force IP forwarding
    """
    global current_hotspot_uuid, forwarding_configured
    global active_connection_path, active_connection_proxy, active_connection_props

    disconnect_wifi_connections()

    # Default to SAE (WPA3) if password exists, otherwise no encryption
    if passwd:
        encrypt = encrypt if encrypt in ["sae", "wpa-psk"] else "sae"
    else:
        logger.info("Creating hotspot without password")
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
        "mode": "ap",
        "band": band,
        "channel": channel
    })

    # Security settings (WPA3/WPA2)
    security_settings = dbus.Dictionary({
        "key-mgmt": encrypt,
        "pairwise": ["ccmp"],
        "proto": ["rsn"]
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
        bus = _get_bus()
        settings_iface = _get_settings_iface()
        nm_iface = _get_nm_iface()

        # Create new connection
        connection_path = settings_iface.AddConnection(connection)

        # Activate the connection
        active_connection_path = nm_iface.ActivateConnection(
            connection_path, device_path, "/"
        )

        # For docker - ip forwarding control
        # Use forwarding_configured flag to prevent repeated pkexec dialogs
        # after sleep/wake, screen lock, or SAE-> WPA-PSK fallback
        if (check_ip_forwarding() or forward) and not forwarding_configured:
            actions_path = os.path.dirname(os.path.abspath(__file__)) + "/Actions.py"
            try:
                command = ["/usr/bin/pkexec", actions_path, "forward"]
                res = subprocess.run(command)
                forwarding_configured = (res.returncode == 0)
                if not forwarding_configured:
                    logger.warning("User cancelled or forwarding config failed (pkexec rc=%d)", res.returncode)
            except Exception as e:
                forwarding_configured = False
                logger.warning("Failed to configure IP forwarding")
                logger.debug(f"Process error details: {e}")

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
                band=band,
                forward=forward
            )
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        raise
    except Exception as e:
        logger.error("Failed to create hotspot")
        logger.debug(f"Error details: {e}")
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
        wifi_band = "bg"

    if encrypt == "WPA-PSK":
        key_mgmt = "wpa-psk"
    elif encrypt == "SAE":
        key_mgmt = "sae"
    else:
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
    global forwarding_configured

    # Keep the flag in sync with the actual kernel state
    # Only show polkit dialog when truly needed.
    forwarding_configured = not check_ip_forwarding()

    # First disable any active connection
    disable_connection()

    try:
        settings_iface = _get_settings_iface()
        if settings_iface:
            remove_all_hotspot_connections()
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        logger.debug(f"Could not remove hotspot connections: {e}")
    except Exception as e:
        logger.debug(f"Could not remove hotspot connections: {e}")

    # Then disconnect device if active
    if device_iface is not None and device_proxy is not None:
        try:
            props = dbus.Interface(device_proxy, "org.freedesktop.DBus.Properties")
            state = props.Get("org.freedesktop.NetworkManager.Device", "State")
            if state == 100:  # NM_DEVICE_STATE_ACTIVATED
                device_iface.Disconnect()
        except dbus.exceptions.DBusException as e:
            if _is_recoverable_error(e):
                _reset_connection()
            elif "NotActive" not in str(e):
                logger.warning("Failed to disconnect network device")
                logger.debug(f"Error details: {e}")

    # Reset connection variables
    active_connection_path = None
    active_connection_proxy = None
    active_connection_props = None

    return True


def remove_all_hotspot_connections():
    """Delete old hotspot profiles."""
    try:
        bus = _get_bus()
        settings_iface = _get_settings_iface()
        connection_paths = settings_iface.ListConnections()
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        logger.error("Failed to list network connections")
        logger.debug(f"DBus error details: {e}")
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
        except dbus.exceptions.DBusException as e:
            if _is_recoverable_error(e):
                _reset_connection()
                break  # Remaining connections will be deleted on next call
            logger.warning(f"Failed to delete connection: {path}")
            logger.debug(f"DBus error details: {e}")
            continue


def get_connection_state():
    """Get the current state of the network connection."""
    if active_connection_props is None:
        return 0
    try:
        return active_connection_props.Get(
            "org.freedesktop.NetworkManager.Connection.Active", "State"
        )
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            _reset_connection()
        return 0


def is_connection_activated():
    """Check if hotspot is successfully activated."""
    return get_connection_state() == 2  # NM_ACTIVE_CONNECTION_STATE_ACTIVATED


def is_wifi_enabled():
    """Check if WiFi hardware is enabled and available."""
    try:
        nm_props = _get_nm_props()
        return nm_props.Get("org.freedesktop.NetworkManager", "WirelessEnabled")
    except dbus.exceptions.DBusException as e:
        if _is_recoverable_error(e):
            logger.info("DBus connection lost, will reconnect on next call")
            _reset_connection()
        logger.warning("WiFi status check failed")
        logger.debug(f"DBus error details: {e}")
        return False


def cleanup():
    """
    Clean up DBus connections when application exits
    Should be called before application quit.
    """
    global forwarding_configured
    forwarding_configured = False
    _reset_connection()
    logger.info("DBus connections cleaned up")
