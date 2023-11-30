import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os

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

        # Comboboxes
        self.network_combo = self.builder.get_object("network_combo")
        self.band_combo = self.builder.get_object("band_combo")
        self.routing_combo = self.builder.get_object("routing_combo")
        self.encrypt_combo = self.builder.get_object("encrypt_combo")

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

        self.routing_combo.append_text("shared")
        self.routing_combo.append_text("manuel")
        self.routing_combo.append_text("automatic")

        self.encrypt_combo.append_text("WPA-PSK")
        self.encrypt_combo.append_text("SAE")


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

        if self.create_button.get_label() == "Disable Connection":
            print("Write disable button functionality here ..")
            enable_icon_name = "network-wireless-disabled-symbolic"
            self.create_button.set_label("Create Hotspot")

        else:
            # ---------- IF HOTSPOT IS ENABLED --------------------------------

            # If hotspot is enabled, change the icon of the gtk image widget
            enable_icon_name = "network-wireless-signal-good-symbolic"
            # Change button name to disable connection
            self.create_button.set_label("Disable Connection")
            # -----------------------------------------------------------------

        self.connection_img.set_from_icon_name(enable_icon_name, Gtk.IconSize.BUTTON)

