import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GdkPixbuf


class HotspotSettings(Gtk.Window):

    def __init__(self):
        super().__init__(title="Hotspot Settings")

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_size(300, 300)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        grid = Gtk.Grid(column_spacing=20, row_spacing=10)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_margin_start(50)
        grid.set_margin_end(50)
        vbox.pack_start(grid, True, True, 0)

        # Network Mode
        mode_label = Gtk.Label(label="Network Mode:")
        mode_label.set_halign(Gtk.Align.START)
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append_text("access point")
        self.mode_combo.append_text("infrastructure")
        self.mode_combo.set_active(0)

        # Band Selection
        band_label = Gtk.Label(label="Band Selection:")
        band_label.set_halign(Gtk.Align.START)
        self.band_combo = Gtk.ComboBoxText()
        self.band_combo.append_text("bg")
        self.band_combo.append_text("a")
        self.band_combo.set_active(0)

        # IPv4 Routing Method
        ipv4_label = Gtk.Label(label="IPv4 Routing Method:")
        ipv4_label.set_halign(Gtk.Align.START)
        self.ipv4_combo = Gtk.ComboBoxText()
        self.ipv4_combo.append_text("shared")
        self.ipv4_combo.append_text("manual")
        self.ipv4_combo.append_text("automatic")
        self.ipv4_combo.set_active(0)

        # Auto Connect
        autoconnect_label = Gtk.Label(label="Auto Connect:")
        autoconnect_label.set_halign(Gtk.Align.START)
        self.autoconnect_switch = Gtk.Switch()
        self.autoconnect_switch.set_active(True)

        # Encryption Method
        encryption_label = Gtk.Label(label="Encryption Method:")
        encryption_label.set_halign(Gtk.Align.START)
        self.encryption_combo = Gtk.ComboBoxText()
        self.encryption_combo.append_text("WPA-PSK")
        self.encryption_combo.append_text("SAE")
        self.encryption_combo.set_active(0)

        # Save Button
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        grid.attach(save_button, 0, 5, 2, 1)

        # Add elements to the grid
        elements = [
            mode_label, self.mode_combo,
            band_label, self.band_combo,
            ipv4_label, self.ipv4_combo,
            autoconnect_label, self.autoconnect_switch,
            encryption_label, self.encryption_combo,
        ]

        for i, element in enumerate(elements):
            grid.attach(element, i % 2, i // 2, 1, 1)


    def on_save_clicked(self, button):
        print("Settings saved")
        self.destroy()


class HotspotApp(Gtk.Window):

    def __init__(self, app):
        super().__init__(application=app)

        # Window Settings
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_size(350, 350)

        # HeaderBar Configuration
        header = Gtk.HeaderBar(title="Pardus Hotspot App")
        header.set_show_close_button(True)
        settings_button = Gtk.Button.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        settings_button.connect("clicked", self.open_settings)
        header.pack_start(settings_button)
        self.set_titlebar(header)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Image Display
        image_path = "./img/hotspot-green.png"
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(image_path, 100, 100)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        vbox.pack_start(image, False, False, 10)

        # Grid for Form Fields
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(50)
        grid.set_margin_end(50)
        vbox.pack_start(grid, True, True, 0)

        # Interface Name
        self.if_name_label = Gtk.Label(label="Interface Name:")
        self.if_name_label.set_halign(Gtk.Align.START)
        grid.attach(self.if_name_label, 0, 0, 1, 1)

        self.if_name_entry = Gtk.Entry()
        grid.attach(self.if_name_entry, 1, 0, 1, 1)

        # Connection Name
        self.con_name_label = Gtk.Label(label="Connection Name:")
        self.con_name_label.set_halign(Gtk.Align.START)
        grid.attach(self.con_name_label, 0, 1, 1, 1)

        self.con_name_entry = Gtk.Entry()
        grid.attach(self.con_name_entry, 1, 1, 1, 1)

        # Password
        self.passwd_label = Gtk.Label(label="Password:")
        self.passwd_label.set_halign(Gtk.Align.START)
        grid.attach(self.passwd_label, 0, 2, 1, 1)

        self.passwd_entry = Gtk.Entry()
        self.passwd_entry.set_visibility(False)
        grid.attach(self.passwd_entry, 1, 2, 1, 1)

        # Create Hotspot Button
        self.create_button = Gtk.Button(label="Create Hotspot")
        self.create_button.connect("clicked", self.on_create_button_clicked)
        grid.attach(self.create_button, 0, 3, 2, 1)


    def on_create_button_clicked(self, widget):
        print("Create button clicked")


    def open_settings(self, button):
            settings_window = HotspotSettings()
            settings_window.show_all()
