import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os

from hotspot import create_hotspot, remove_hotspot, set_network_interface, is_wifi_enabled
from network_utils import get_interface_names

import locale
from locale import gettext as _


class MainWindow:
    def __init__(self, application):

        self.builder = Gtk.Builder()

        # Import UI file:
        glade_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "MainWindow.glade")
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("main_window")
        self.window.set_application(application)
        self.window.set_position(Gtk.WindowPosition.CENTER)

        # Img to change due to connection success
        self.connection_img = self.builder.get_object("connection_img")
        self.switch_img = self.builder.get_object("switch_img")
        self.warning_img = self.builder.get_object("warning_img")

        # Buttons
        self.switch_button = self.builder.get_object("switch_button")
        self.create_button = self.builder.get_object("create_button")
        self.ok_button = self.builder.get_object("ok_button")

        # Stack for switching between settings and main boxes
        self.hotspot_stack = self.builder.get_object("hotspot_stack")

        # Boxes
        self.main_box = self.builder.get_object("main_box")
        self.settings_box = self.builder.get_object("settings_box")
        self.connection_box = self.builder.get_object("connection_box")
        self.errors_box = self.builder.get_object("errors_box")

        # Comboboxes (Gtk.ComboBoxText)
        self.ifname_combo = self.builder.get_object("ifname_combo")
        self.network_combo = self.builder.get_object("network_combo")
        self.band_combo = self.builder.get_object("band_combo")
        self.encrypt_combo = self.builder.get_object("encrypt_combo")

        # Entries
        self.password_entry = self.builder.get_object("password_entry")
        self.connection_entry = self.builder.get_object("connection_entry")

        # Labels
        # self.status_lbl = self.builder.get_object("status_lbl")
        self.warning_msgs_lbl = self.builder.get_object("warning_msgs_lbl")

        # Switch
        self.auto_switch = self.builder.get_object("auto_switch")

        # Signals
        self.switch_button.connect("clicked", self.on_switch_button_clicked)
        self.create_button.connect("clicked", self.on_create_button_clicked)
        self.ok_button.connect("clicked", self.on_ok_button_clicked)
        self.password_entry.connect("icon-press", self.password_entry_icon_press)
        self.password_entry.connect("icon-release", self.password_entry_icon_release)

        # Fill comboboxes
        self.network_combo.append_text("access point")
        self.network_combo.append_text("infrastructure")

        self.band_combo.append_text("bg")
        self.band_combo.append_text("a")

        self.encrypt_combo.append_text("WPA-PSK")
        self.encrypt_combo.append_text("SAE")

        get_interface_names(self.ifname_combo, self.window)

        self.window.show_all()


    def on_main_window_destroy(self, widget):
        self.window.get_application().quit()


    def password_entry_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(1, "view-reveal-symbolic")


    def password_entry_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(1, "view-conceal-symbolic")


    def on_switch_button_clicked(self, button):
        current_page = self.hotspot_stack.get_visible_child_name()

        if current_page == "page_settings":
            self.hotspot_stack.set_visible_child_name("page_main")
        else:
            self.hotspot_stack.set_visible_child_name("page_settings")


    def on_create_button_clicked(self, button):
        # If hotspot is disabled
        if self.create_button.get_label() == "Disable Connection":
            enable_icon_name = "network-wireless-disabled-symbolic"
            remove_hotspot()
            self.create_button.set_label("Create Hotspot")

            # self.status_lbl.set_markup("<span
            # color='red'>{}</span>".format("Disable"))

        # If hotspot is enabled
        else:
            # Change the icon of the gtk image widget
            enable_icon_name = "network-wireless-signal-good-symbolic"

            ssid = self.connection_entry.get_text()  # Connection Name
            password = self.password_entry.get_text()
            ifname = self.ifname_combo.get_active_text()

            print("connection state: ", is_wifi_enabled())

            # Check if Wi-Fi is enabled
            if not is_wifi_enabled():
                message = _("Please enable Wi-Fi to continue.")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.switch_button.set_visible(False)
                return

            # Check if an interface is selected
            if self.ifname_combo.get_active() == -1:
                message = _("Please select a network interface for the hotspot")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.switch_button.set_visible(False)
                return

            # Check if connection name is empty
            if len(ssid) == 0:
                message = _("Please enter a name for your hotspot connection")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.switch_button.set_visible(False)
                return

            # Check if password is either 0 or at least 8 characters
            if len(password) != 0 and len(password) < 8:
                message = _("Password must be empty or at least 8 characters long")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.switch_button.set_visible(False)
                return

            set_network_interface(ifname)

            create_hotspot(ssid, password)
            self.create_button.set_label("Disable Connection")
            # self.status_lbl.set_markup("<span color='green'>{}</span>".format("Active"))

        self.connection_img.set_from_icon_name(enable_icon_name,
                                               Gtk.IconSize.BUTTON)


    def on_ok_button_clicked(self, button):
        # Send a speacial flag if you want to exit !
        self.hotspot_stack.set_visible_child_name("page_main")
