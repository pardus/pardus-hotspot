import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GdkPixbuf
import os
import qrcode
import io

import hotspot
from network_utils import get_interface_names
from hotspot_settings import HotspotSettings

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator
except:
    # fall back to Ayatana
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as appindicator

import locale
from locale import gettext as _
locale.bindtextdomain('pardus-hotspot', '/usr/share/locale')
locale.textdomain('pardus-hotspot')
_ = locale.gettext


def getenv(env_name):
    env = os.environ.get(env_name)
    return env if env else ""

xfce_desktop = False
if "xfce" in getenv("SESSION").lower() or "xfce" in getenv("XDG_CURRENT_DESKTOP").lower():
    xfce_desktop = True


class MainWindow:
    def __init__(self, application):
        self.builder = Gtk.Builder()

        # Import UI file:
        glade_file = (
            os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        )

        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        self.define_components()
        self.init_settings()

        self.window.set_application(application)

        self.init_indicator()
        self.set_indicator()

        # Check if there is an existing hotspot
        # if not, takes info from the last connection (settings.ini)
        self.check_existing_hotspot()

        # Start the Wi-Fi checker with a timeout (every 5 seconds)
        GLib.timeout_add_seconds(5, self.check_wifi_and_update_hotspot)

        self.window.show()

    def define_components(self):
        # Take last connection settings
        self.hotspot_settings = HotspotSettings()
        self.hotspot_settings.read_config()

        # Window
        self.window = self.builder.get_object("main_window")
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_resizable(False)

        # Img to change due to connection success
        self.connection_img = self.builder.get_object("connection_img")
        self.menu_img = self.builder.get_object("menu_img")
        self.warning_img = self.builder.get_object("warning_img")
        self.settings_img = self.builder.get_object("settings_img")
        self.qr_image = self.builder.get_object("qr_Image") 

        # Buttons
        self.menu_button = self.builder.get_object("menu_button")
        self.create_button = self.builder.get_object("create_button")
        self.ok_button = self.builder.get_object("ok_button")
        self.menu_about = self.builder.get_object("menu_about")
        self.menu_settings = self.builder.get_object("menu_settings")
        self.home_button = self.builder.get_object("home_button")
        self.restore_button = self.builder.get_object("restore_button")

        # Stack for switching between settings and main boxes
        self.hotspot_stack = self.builder.get_object("hotspot_stack")
        self.connection_stack = self.builder.get_object("connection_stack")

        # Boxes
        self.main_box = self.builder.get_object("main_box")
        self.settings_box = self.builder.get_object("settings_box")
        self.connection_box = self.builder.get_object("connection_box")
        self.errors_box = self.builder.get_object("errors_box")
        self.connected_box = self.builder.get_object("connected_box")
        self.forwarding_box = self.builder.get_object("forwarding_box")

        # Comboboxes (Gtk.ComboBoxText)
        self.ifname_combo = self.builder.get_object("ifname_combo")
        self.band_combo = self.builder.get_object("band_combo")
        self.encrypt_combo = self.builder.get_object("encrypt_combo")

        # Entries
        self.password_entry = self.builder.get_object("password_entry")
        self.connection_entry = self.builder.get_object("connection_entry")
        self.con_entry = self.builder.get_object("con_entry")
        self.con_password_entry = self.builder.get_object("con_password_entry")
        self.security_entry = self.builder.get_object("security_entry")

        # Labels
        # self.status_lbl = self.builder.get_object("status_lbl")
        self.warning_msgs_lbl = self.builder.get_object("warning_msgs_lbl")
        self.settings_lbl = self.builder.get_object("settings_lbl")
        self.con_name_lbl = self.builder.get_object("con_name_lbl")
        self.con_password_lbl = self.builder.get_object("con_password_lbl")
        self.security_lbl = self.builder.get_object("security_lbl")
        self.forwarding_lbl = self.builder.get_object("forwarding_lbl")

        # Switch
        self.startup_switch = self.builder.get_object("startup_switch")
        self.forwarding_switch = self.builder.get_object("forwarding_switch")

        # Dialog
        self.hotspot_dialog = self.builder.get_object("hotspot_dialog")
        self.hotspot_dialog.set_transient_for(self.window)
        self.hotspot_dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)

        # Header Bar
        self.header_bar = self.builder.get_object("header_bar")

        # Popover
        self.menu_popover = self.builder.get_object("menu_popover")

        # Set version if it cannot be retrieved from __version__ file,
        # then use MainWindow.glade file
        try:
            version = open(
                os.path.dirname(os.path.abspath(__file__)) + "/__version__"
                ).readline()
            self.hotspot_dialog.set_version(version)
        except:
            pass

        # Signals
        self.menu_about.connect("clicked", self.on_menu_about_clicked)
        self.menu_settings.connect("clicked", self.on_menu_settings_clicked)
        self.create_button.connect("clicked", self.on_create_button_clicked)
        self.ok_button.connect("clicked", self.on_ok_button_clicked)
        self.password_entry.connect("changed", self.on_password_entry_changed)
        self.password_entry.connect("icon-press", self.password_entry_icon_press)
        self.password_entry.connect("icon-release", self.password_entry_icon_release)
        self.connection_entry.connect("changed", self.on_password_entry_changed)
        self.con_password_entry.connect("icon-press", self.password_entry_icon_press)
        self.con_password_entry.connect("icon-release", self.password_entry_icon_release)
        self.startup_switch.connect("state-set", self.on_startup_switch_state_set)
        self.restore_button.connect("clicked", self.on_restore_button_clicked)
        self.home_button.connect("clicked", self.on_home_button_clicked)
        self.band_combo.connect("changed", lambda widget: self.on_settings_changed())
        self.encrypt_combo.connect("changed", lambda widget: self.on_settings_changed())
        # self.startup_switch.connect("changed", self.on_settings_changed)
        self.forwarding_switch.connect("state-set", self.on_forwarding_switch_state_set)

        self.band_combo.append_text("2.4GHz")
        self.band_combo.append_text("5GHz")

        self.encrypt_combo.append_text("WPA-PSK")
        self.encrypt_combo.append_text("SAE")

        self.band_combo.set_active(0)       # Set default: 2.4Ghz
        self.encrypt_combo.set_active(1)    # Set default: SAE

        self.qr_image.set_visible(False)

        get_interface_names(self.ifname_combo, self.window)


    def init_settings(self):
        self.connection_entry.set_text(self.hotspot_settings.ssid)
        self.password_entry.set_text(self.hotspot_settings.password)
        self.get_comboboxtext_value(
            self.ifname_combo,
            self.hotspot_settings.interface
        )
        self.get_comboboxtext_value(
            self.encrypt_combo,
            self.hotspot_settings.encryption
        )
        self.get_comboboxtext_value(
            self.band_combo,
            self.hotspot_settings.band
        )

        iptables_paths = [
            "/usr/sbin/iptables",
            "/usr/bin/iptables",
            "/sbin/iptables",
            "/bin/iptables"
        ]

        if not any(os.path.exists(path) for path in iptables_paths):
            self.forwarding_box.set_visible(False)

        self.startup_switch.set_active(self.hotspot_settings.autostart)
        self.forwarding_switch.set_active(self.hotspot_settings.forwarding)


    def get_comboboxtext_value(self, widget, settings_val):
        model = widget.get_model()
        index = 0
        for row in model:
            if row[0] == settings_val:
                widget.set_active(index)
                break
            index += 1


    def init_indicator(self):
        icon_name = "pardus-hotspot-off-symbolic" if xfce_desktop else "pardus-hotspot-status-off-symbolic"
        self.indicator = appindicator.Indicator.new(
            "pardus-hotspot", icon_name,
            appindicator.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_title(_("Pardus Hotspot"))

        # Create a menu for the indicator
        self.menu = Gtk.Menu()

        # Show App Menu Item
        self.item_show_app = Gtk.MenuItem(label=_("Show App"))
        self.item_show_app.connect("activate", self.on_menu_show_app)

        self.item_settings = Gtk.MenuItem(label=_("Settings"))
        self.item_settings.connect("activate", self.on_menu_settings_clicked)

        self.item_enable = Gtk.MenuItem(label=_("Enable"))
        self.item_enable.connect("activate", self.on_create_button_clicked)

        self.item_separator1 = Gtk.SeparatorMenuItem()

        # Quit App Menu Item
        self.item_quit = Gtk.MenuItem(label=_("Quit"))
        self.item_quit.connect("activate", self.on_window_destroy)

        self.menu.append(self.item_show_app)
        self.menu.append(self.item_settings)
        self.menu.append(self.item_enable)
        self.menu.append(self.item_separator1)
        self.menu.append(self.item_quit)

        self.menu.show_all()
        self.indicator.set_menu(self.menu)


    def set_indicator(self):
        if self.window.is_visible():
            self.item_show_app.set_label(_("Show App"))
        else:
            self.item_show_app.set_label(_("Hide App"))


    def on_menu_show_app(self, *args):
        window_state = self.window.is_visible()
        if window_state:
            self.window.set_visible(False)
            self.item_show_app.set_label(_("Show App"))
        else:
            self.window.set_visible(True)
            self.item_show_app.set_label(_("Hide App"))


    def on_window_delete_event(self, widget=None, event=None):
        self.window.hide()
        self.item_show_app.set_label(_("Show App"))
        return True

    def on_window_destroy(self, widget, event=None):
        # Save last connection settings
        self.hotspot_settings.ssid = self.connection_entry.get_text()
        self.hotspot_settings.password = self.password_entry.get_text()
        self.hotspot_settings.interface = self.ifname_combo.get_active_text()
        self.hotspot_settings.encryption = self.encrypt_combo.get_active_text()
        self.hotspot_settings.band = self.band_combo.get_active_text()
        self.hotspot_settings.write_config()

        if self.hotspot_dialog.is_visible():
            self.hotspot_dialog.hide()

        hotspot.remove_hotspot()
        self.window.get_application().quit()

    def on_startup_switch_state_set(self, switch, state):
        self.hotspot_settings.autostart = state
        self.hotspot_settings.set_autostart(state)

    def on_forwarding_switch_state_set(self, switch, state):
        self.hotspot_settings.forwarding = state
        self.hotspot_settings.write_config()
        return False

    def check_existing_hotspot(self):
        """
        Check if there is an existing hotspot connection, if so,
        update UI with its information.
        """
        # TODO: Write a func to update UI elements, use it everywhere

        hotspot_info = hotspot.get_active_hotspot_info()
        style_context = self.create_button.get_style_context()

        if hotspot_info:
            ssid = hotspot_info["ssid"]
            password = hotspot_info["password"]
            encryption = hotspot_info["encryption"]

            if encryption == "wpa-psk":
                display_encryption = "WPA-PSK"
            elif encryption == "sae":
                display_encryption = "SAE"
            else:
                display_encryption = "SAE"

            # Update input fields
            self.connection_entry.set_text(ssid)
            self.password_entry.set_text(password)
            if encryption:
                self.get_comboboxtext_value(self.encrypt_combo, display_encryption)

            # Update connection info
            self.connection_stack.set_visible_child_name("page_connected")
            self.con_entry.set_text(ssid)
            self.con_entry.set_sensitive(False)
            self.con_password_entry.set_text(password)
            self.con_password_entry.set_editable(False)
            self.security_entry.set_text(display_encryption)
            self.security_entry.set_sensitive(False)

            # Update connection icon
            if xfce_desktop:
                self.indicator.set_icon("pardus-hotspot-on-symbolic")
            else:
                self.indicator.set_icon("pardus-hotspot-status-on-symbolic")

            # Update buttons and indicators
            self.create_button.set_label(_("Disable Connection"))
            self.item_enable.set_label(_("Disable"))
            self.connection_img.set_from_icon_name(
                "network-wireless-signal-good-symbolic", Gtk.IconSize.BUTTON
            )

            style_context.remove_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
            style_context.add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)

            # Generate and show QR
            self.qr_image.set_visible(True)
            self.generate_qr_code(ssid, password, display_encryption)

            # Save settings to config file - override latest conn.
            self.hotspot_settings.ssid = ssid
            self.hotspot_settings.password = password
            self.hotspot_settings.encryption = display_encryption
            if "interface" in hotspot_info:
                self.hotspot_settings.interface = hotspot_info["interface"]
                self.get_comboboxtext_value(self.ifname_combo, hotspot_info["interface"])
            if "band" in hotspot_info:
                band_display = "2.4GHz" if hotspot_info["band"] == "bg" else "5GHz"
                self.hotspot_settings.band = band_display
                self.get_comboboxtext_value(self.band_combo, band_display)
            self.hotspot_settings.write_config()
        else:
            self.create_button.set_label(_("Create Hotspot"))
            self.item_enable.set_label(_("Enable"))
            self.qr_image.set_visible(False)
            self.qr_image.clear()
            self.connection_img.set_from_icon_name(
                "network-wireless-disabled-symbolic", Gtk.IconSize.BUTTON
            )

            style_context.remove_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
            style_context.add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

            # Enable input fields
            self.con_entry.set_sensitive(True)
            self.con_entry.set_editable(True)
            self.con_password_entry.set_sensitive(True)
            self.con_password_entry.set_editable(True)
            self.security_entry.set_sensitive(True)
            self.security_entry.set_editable(True)

            self.connection_stack.set_visible_child_name("page_connect")

            # Update connection icon
            if xfce_desktop:
                self.indicator.set_icon("pardus-hotspot-off-symbolic")
            else:
                self.indicator.set_icon("pardus-hotspot-status-off-symbolic")


    def check_wifi_and_update_hotspot(self):
        """
        Regularly checks Wi-Fi status and updates the hotspot state and UI
        elements accordingly.
        """
        if not hotspot.is_wifi_enabled():
            hotspot.remove_hotspot()
            self.create_button.set_label(_("Create Hotspot"))
            self.connection_img.set_from_icon_name(
                "network-wireless-disabled-symbolic", Gtk.IconSize.BUTTON
            )
            self.qr_image.set_visible(False)
        else:
            self.check_existing_hotspot()

            if self.create_button.get_label() == _("Disable Connection"):
                self.qr_image.set_visible(True)
            else:
                self.qr_image.set_visible(False)
                self.qr_image.clear()


        return True


    def password_entry_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(1, "view-reveal-symbolic")


    def password_entry_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(1, "view-conceal-symbolic")


    def on_password_entry_changed(self, entry):
        """
        Changes connect button's style based on the password length and whether
        the connection name is provided
        """
        password = self.password_entry.get_text()
        connection_name = self.connection_entry.get_text()

        style_context = self.create_button.get_style_context()
        style_context.remove_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        style_context.remove_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)

        if connection_name and len(password) >= 8:
            style_context.add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        elif self.create_button.get_label() == _("Disable Connection"):
            style_context.add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)


    def on_menu_about_clicked(self, button):
        self.menu_popover.popdown()
        self.hotspot_dialog.run()
        self.hotspot_dialog.hide()


    def on_menu_settings_clicked(self, button):
        """
        Switches between the main and settings pages, updating the title
        accordingly.
        """
        self.menu_popover.popdown()

        self.settings_lbl.set_text(_("Home Page"))
        self.item_settings.set_label(_("Home Page"))
        self.settings_img.set_from_icon_name("user-home-symbolic",
            Gtk.IconSize.BUTTON
        )
        current_page = self.hotspot_stack.get_visible_child_name()
        if current_page == "page_settings":
            self.settings_img.set_from_icon_name("preferences-other-symbolic",
                Gtk.IconSize.BUTTON
            )
            self.settings_lbl.set_text(_("Settings"))
            self.item_settings.set_label(_("Settings"))
            self.header_bar.set_title(_("Pardus Hotspot"))
            self.hotspot_stack.set_visible_child_name("page_main")
        else:
            self.header_bar.set_title(_("Hotspot Settings"))
            self.hotspot_stack.set_visible_child_name("page_settings")

        self.item_show_app.set_label(_("Hide App"))

        self.window.set_visible(True)
        self.window.present()


    def on_restore_button_clicked(self, button):
        self.band_combo.set_active(0)           # Set default: 2.4Ghz
        self.encrypt_combo.set_active(1)        # Set default: SAE
        self.startup_switch.set_active(False)   # Set default: False
        self.forwarding_switch.set_active(False) # Set default: False

    def generate_qr_code(self, ssid, password, encryption):
        # Format the Wi-Fi connection string
        if encryption == "SAE":
            wifi_string = f"WIFI:S:{ssid};T:SAE;P:{password};H:true;;"
        elif encryption == "WPA-PSK":
            wifi_string = f"WIFI:S:{ssid};T:WPA;P:{password};H:false;;"
        else:
            wifi_string = f"WIFI:S:{ssid};T:nopass;;"

        # Generate QR code with smaller box size and border
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(wifi_string)
        qr.make(fit=True)

        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Convert PIL image to GdkPixbuf
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)

        loader = GdkPixbuf.PixbufLoader.new_with_type('png')
        loader.write(buffer.read())
        loader.close()

        pixbuf = loader.get_pixbuf()

        scaled_pixbuf = pixbuf.scale_simple(120, 120, GdkPixbuf.InterpType.BILINEAR)

        # Set the QR code image to the Gtk.Image widget
        self.qr_image.set_from_pixbuf(scaled_pixbuf)


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
        style_context = self.create_button.get_style_context()

        if self.create_button.get_label() == _("Disable Connection"):
            enable_icon_name = "network-wireless-disabled-symbolic"
            hotspot.remove_hotspot()
            self.connection_stack.set_visible_child_name("page_connect")
            self.create_button.set_label(_("Create Hotspot"))
            self.item_enable.set_label(_("Enable"))
            self.qr_image.set_visible(False)
            self.qr_image.clear()

            style_context.remove_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
            style_context.add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        else:
            enable_icon_name = "network-wireless-signal-good-symbolic"

            ssid = self.connection_entry.get_text()  # Connection Name
            password = self.password_entry.get_text()
            ifname = self.ifname_combo.get_active_text()
            encrypt = self.encrypt_combo.get_active_text()
            band = self.band_combo.get_active_text()

            # Determine wifi band and encryption based on user selection
            # Choose "sae" for apple products
            selected_band = "bg" if band == "2.4GHz" else "a"
            selected_encrypt = (
                    "wpa-psk" if encrypt == "WPA-PSK"
                    else "sae" if encrypt == "SAE"
                    else "sae"
            )

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

            # After successful connection setup, change the button to red
            style_context.add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
            style_context.remove_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)

            # Check if forwarding is enabled
            forwarding_enabled = self.forwarding_switch.get_active()

            hotspot.set_network_interface(ifname)
            hotspot.create_hotspot(ssid, password, selected_encrypt, selected_band, forwarding_enabled)

            self.connection_stack.set_visible_child_name("page_connected")
            self.con_entry.set_text(ssid)
            self.con_entry.set_sensitive(False)
            self.con_password_entry.set_text(password)
            self.con_password_entry.set_editable(False)
            self.security_entry.set_text(encrypt)
            self.security_entry.set_sensitive(False)

            self.hotspot_settings.ssid = ssid
            self.hotspot_settings.password = password
            self.hotspot_settings.interface = ifname
            self.hotspot_settings.encryption = encrypt
            self.hotspot_settings.write_config()

            self.create_button.set_label(_("Disable Connection"))
            self.item_enable.set_label(_("Disable"))
            self.qr_image.set_visible(True)

            # Generate initial QR code
            ssid = self.connection_entry.get_text()
            password = self.password_entry.get_text()
            encrypt = self.encrypt_combo.get_active_text()
            self.generate_qr_code(ssid, password, encrypt)

        self.connection_img.set_from_icon_name(enable_icon_name, Gtk.IconSize.BUTTON)


    def on_ok_button_clicked(self, button):
        # Send a speacial flag if you want to exit !
        self.hotspot_stack.set_visible_child_name("page_main")
        self.menu_button.set_visible(True)


    def on_settings_changed(self):
        """
        Applies changes to hotspot settings and updates the UI to reflect these
        changes.
        """
        # Remove current connection
        hotspot.remove_hotspot()
        enable_icon_name = "network-wireless-disabled-symbolic"
        self.settings_img.set_from_icon_name("preferences-other-symbolic",
                Gtk.IconSize.BUTTON
        )
        self.create_button.set_label(_("Create Hotspot"))
        self.connection_img.set_from_icon_name(enable_icon_name, Gtk.IconSize.BUTTON)

        style_context = self.create_button.get_style_context()
        style_context.remove_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)

        self.on_password_entry_changed(self.password_entry)

        # Get selected values from the comboboxes
        selected_band = self.band_combo.get_active_text()
        selected_encrypt = self.encrypt_combo.get_active_text()

        ssid = self.connection_entry.get_text()
        password = self.password_entry.get_text()

        self.con_entry.set_text(ssid)
        self.con_entry.set_sensitive(True)
        self.con_password_entry.set_text(password)
        self.con_password_entry.set_editable(True)
        self.security_entry.set_text(str(selected_encrypt))

        # Update the hotspot settings
        hotspot.update_hotspot_settings(selected_band, selected_encrypt)


    def on_home_button_clicked(self, button):
        self.hotspot_stack.set_visible_child_name("page_main")
        self.header_bar.set_title(_("Pardus Hotspot"))
        self.settings_img.set_from_icon_name("preferences-other-symbolic",
            Gtk.IconSize.BUTTON
        )
        self.settings_lbl.set_text(_("Settings"))
        self.item_settings.set_label(_("Settings"))
