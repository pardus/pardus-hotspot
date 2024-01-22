import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import os

import hotspot
from network_utils import get_interface_names

import locale
from locale import gettext as _


class MainWindow:
    def __init__(self, application):
        self.builder = Gtk.Builder()

        # Import UI file:
        glade_file = (
            os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        )

        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("main_window")
        self.window.set_application(application)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_resizable(False)

        self.defineComponents()

        # Start the Wi-Fi checker with a timeout (every 5 seconds)
        GLib.timeout_add_seconds(5, self.check_wifi_and_update_hotspot)

        self.window.show_all()


    def defineComponents(self):
        # Img to change due to connection success
        self.connection_img = self.builder.get_object("connection_img")
        self.menu_img = self.builder.get_object("menu_img")
        self.warning_img = self.builder.get_object("warning_img")

        # Buttons
        self.menu_button = self.builder.get_object("menu_button")
        self.create_button = self.builder.get_object("create_button")
        self.ok_button = self.builder.get_object("ok_button")
        self.menu_about = self.builder.get_object("menu_about")
        self.menu_settings = self.builder.get_object("menu_settings")
        self.save_button = self.builder.get_object("save_button")

        # Stack for switching between settings and main boxes
        self.hotspot_stack = self.builder.get_object("hotspot_stack")

        # Boxes
        self.main_box = self.builder.get_object("main_box")
        self.settings_box = self.builder.get_object("settings_box")
        self.connection_box = self.builder.get_object("connection_box")
        self.errors_box = self.builder.get_object("errors_box")

        # Comboboxes (Gtk.ComboBoxText)
        self.ifname_combo = self.builder.get_object("ifname_combo")
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

        # Dialog
        self.hotspot_dialog = self.builder.get_object("hotspot_dialog")
        self.hotspot_dialog.set_transient_for(self.window)
        self.hotspot_dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

        # Header Bar
        self.header_bar = self.builder.get_object("header_bar")

        # Popover
        self.menu_popover = self.builder.get_object("menu_popover")

        # Signals
        self.menu_about.connect("clicked", self.on_menu_about_clicked)
        self.menu_settings.connect("clicked", self.on_menu_settings_clicked)
        self.create_button.connect("clicked", self.on_create_button_clicked)
        self.ok_button.connect("clicked", self.on_ok_button_clicked)
        self.password_entry.connect("icon-press", self.password_entry_icon_press)
        self.password_entry.connect("icon-release", self.password_entry_icon_release)
        self.save_button.connect("clicked", self.on_save_button_clicked)
        self.window.connect("destroy", self.on_main_window_destroy)

        self.band_combo.append_text("2.4GHz")
        self.band_combo.append_text("5GHz")

        self.encrypt_combo.append_text("WPA-PSK")
        self.encrypt_combo.append_text("SAE")

        get_interface_names(self.ifname_combo, self.window)


    def on_main_window_destroy(self, widget):
        # Remove connected hotspot before destroying the window
        hotspot.remove_hotspot()
        self.window.get_application().quit()


    def check_wifi_and_update_hotspot(self):
        """
        Regularly checks Wi-Fi status and updates the hotspot state and UI
        elements accordingly.
        """
        if not hotspot.is_wifi_enabled():
            print("Wi-Fi is off. Disabling hotspot.")
            hotspot.remove_hotspot()
            # Update GUI for disconnection
            self.create_button.set_label("Create Hotspot")
            self.connection_img.set_from_icon_name(
                "network-wireless-disabled-symbolic", Gtk.IconSize.BUTTON
            )
        return True


    def password_entry_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(1, "view-reveal-symbolic")


    def password_entry_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(1, "view-conceal-symbolic")


    def on_menu_about_clicked(self, button):
        self.menu_popover.popdown()
        self.hotspot_dialog.run()
        self.hotspot_dialog.hide()


    def on_menu_settings_clicked(self, button):
        """
        Siwtches between the main and settings pages, updating the title
        accordingly.
        """
        current_page = self.hotspot_stack.get_visible_child_name()

        if current_page == "page_settings":
            self.header_bar.set_title("Pardus Hotspot Application")
            self.hotspot_stack.set_visible_child_name("page_main")
        else:
            self.header_bar.set_title("Hotspot Settings")
            self.hotspot_stack.set_visible_child_name("page_settings")


    def on_create_button_clicked(self, button):
        """
        Manages the creation and deactivation of a hotspot connection.
        Toggles the hotspot state based on its current status:
        - If the hotspot is active, it gets disabled and the button label is
        updated to 'Create Hotspot'.
        - If the hotspot is inactive, it performs checks for Wi-Fi status,
        interface selection, connection name, and password validity.
        If all checks pass, it activates the hotspot and updates the button
        label to 'Disable Connection'.
        In both cases, it updates the connection icon accordingly.
        """

        if self.create_button.get_label() == "Disable Connection":
            enable_icon_name = "network-wireless-disabled-symbolic"
            hotspot.remove_hotspot()
            self.create_button.set_label("Create Hotspot")
        else:
            enable_icon_name = "network-wireless-signal-good-symbolic"

            ssid = self.connection_entry.get_text()  # Connection Name
            password = self.password_entry.get_text()
            ifname = self.ifname_combo.get_active_text()

            # Check if Wi-Fi is enabled
            if not hotspot.is_wifi_enabled():
                message = _("Please enable Wi-Fi to continue")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.menu_button.set_visible(False)
                return

            # Check if an interface is selected
            if self.ifname_combo.get_active() == -1:
                message = _("Please select a network interface for the hotspot")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.menu_button.set_visible(False)
                return

            # Check if connection name is empty
            if len(ssid) == 0:
                message = _("Please enter a name for your hotspot connection")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.menu_button.set_visible(False)
                return

            # Check if password is at least 8 characters
            if len(password) < 8:
                message = _("Password must be at least 8 characters long")
                self.hotspot_stack.set_visible_child_name("page_errors")
                self.warning_msgs_lbl.set_text(message)
                self.menu_button.set_visible(False)
                return

            hotspot.set_network_interface(ifname)
            hotspot.create_hotspot(ssid, password)
            self.create_button.set_label("Disable Connection")

        self.connection_img.set_from_icon_name(enable_icon_name, Gtk.IconSize.BUTTON)


    def on_ok_button_clicked(self, button):
        # Send a speacial flag if you want to exit !
        self.hotspot_stack.set_visible_child_name("page_main")


    def on_save_button_clicked(self, button):
        """
        Applies changes to hotspot settings and updates the UI to reflect these
        changes.
        """
        # Remove current connection
        hotspot.remove_hotspot()
        enable_icon_name = "network-wireless-disabled-symbolic"
        hotspot.remove_hotspot()
        self.create_button.set_label("Create Hotspot")
        self.connection_img.set_from_icon_name(enable_icon_name, Gtk.IconSize.BUTTON)

        # Get selected values from the comboboxes
        selected_band = self.band_combo.get_active_text()
        selected_encrypt = self.encrypt_combo.get_active_text()

        # Update the hotspot settings
        hotspot.update_hotspot_settings(selected_band, selected_encrypt)

        # Switch back to the main page
        self.hotspot_stack.set_visible_child_name("page_main")
