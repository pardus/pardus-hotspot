import os
from gi.repository import Gtk

import locale
from locale import gettext as _
locale.bindtextdomain('pardus-hotspot', '/usr/share/locale')
locale.textdomain('pardus-hotspot')
_ = locale.gettext


def get_interface_names(ifname_combo, window):
    ifname_combo.remove_all()

    try:
        interfaces = os.listdir("/sys/class/net/")
    except OSError as e:
        print("Error reading network interfaces:", e)
        interfaces = []

    wifi_interfaces = [
        iface
        for iface in interfaces
        if os.path.exists(f"/sys/class/net/{iface}/wireless")
    ]

    if wifi_interfaces:
        for iface in wifi_interfaces:
            ifname_combo.append_text(iface)
            ifname_combo.set_active(0)
    else:
        ifname_combo.append_text(_("No wireless interfaces available"))
        dialog = Gtk.MessageDialog(
            transient_for=window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Wi-Fi Network Interface Not Found"),
        )
        dialog.format_secondary_text(
            _("Please ensure your computer has a Wi-Fi adapter and it is working correctly.")
        )
        dialog.run()
        dialog.destroy()

        Gtk.main_quit()
