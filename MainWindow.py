import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os

from hotspot import create_hotspot, remove_hotspot, set_iface

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

        # Buttons
        self.switch_button = self.builder.get_object("switch_button")
        self.create_button = self.builder.get_object("create_button")

        # Stack for switching between settings and main boxes
        self.hotspot_stack = self.builder.get_object("hotspot_stack")

        # Boxes
        self.main_box = self.builder.get_object("main_box")
        self.settings_box = self.builder.get_object("settings_box")
        self.connection_box = self.builder.get_object("connection_box")

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

        # Switch
        self.auto_switch = self.builder.get_object("auto_switch")

        # Signals
        self.switch_button.connect("clicked", self.on_switch_button_clicked)
        self.create_button.connect("clicked", self.on_create_button_clicked)

        # Fill comboboxes
        self.network_combo.append_text("access point")
        self.network_combo.append_text("infrastructure")

        self.band_combo.append_text("bg")
        self.band_combo.append_text("a")

        self.encrypt_combo.append_text("WPA-PSK")
        self.encrypt_combo.append_text("SAE")

        self.ifname_combo.append_text("fill_ifname-s_here")

        self.window.show_all()


    def on_main_window_destroy(self, widget):
        self.window.get_application().quit()


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
            ssid = self.connection_entry.get_text()
            password = self.password_entry.get_text()
            ifname= self.ifname_combo.get_active_text()

            set_iface(ifname)

            # Here, pass the SSID and password to the create_hotspot function
            create_hotspot(ssid, password)
            self.create_button.set_label("Disable Connection")
            # self.status_lbl.set_markup("<span color='green'>{}</span>".format("Active"))

        self.connection_img.set_from_icon_name(enable_icon_name,
                                               Gtk.IconSize.BUTTON)
