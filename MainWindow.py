import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GdkPixbuf

class HotspotApp(Gtk.Window):

    def __init__(self, app):
        super().__init__(application=app)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_size(350, 350)

        header = Gtk.HeaderBar(title="Pardus Hotspot App")
        header.set_show_close_button(True)
        self.set_titlebar(header)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        image_path = "./img/hotspot-green.png"
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(image_path, 100, 100)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        vbox.pack_start(image, False, False, 10)

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_start(50)
        grid.set_margin_end(50)
        vbox.pack_start(grid, True, True, 0)

        self.if_name_label = Gtk.Label(label="Interface Name:")
        self.if_name_label.set_halign(Gtk.Align.START)
        grid.attach(self.if_name_label, 0, 0, 1, 1)

        self.if_name_entry = Gtk.Entry()
        grid.attach(self.if_name_entry, 1, 0, 1, 1)

        self.con_name_label = Gtk.Label(label="Connection Name:")
        self.con_name_label.set_halign(Gtk.Align.START)
        grid.attach(self.con_name_label, 0, 1, 1, 1)

        self.con_name_entry = Gtk.Entry()
        grid.attach(self.con_name_entry, 1, 1, 1, 1)

        self.passwd_label = Gtk.Label(label="Password:")
        self.passwd_label.set_halign(Gtk.Align.START)
        grid.attach(self.passwd_label, 0, 2, 1, 1)

        self.passwd_entry = Gtk.Entry()
        self.passwd_entry.set_visibility(False)
        grid.attach(self.passwd_entry, 1, 2, 1, 1)

        self.create_button = Gtk.Button(label="Create Hotspot")
        self.create_button.connect("clicked", self.on_button_clicked)
        grid.attach(self.create_button, 0, 3, 2, 1)


    def on_button_clicked(self, widget):
        print("Create button clicked")
