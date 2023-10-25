import gi
import subprocess
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class HotspotApp(Gtk.Window):

    def __init__(self, app):
        super().__init__(title="Pardus Hotspot Application", application=app)

        self.set_position(Gtk.WindowPosition.CENTER)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.if_name_label = Gtk.Label(label="Interface Name:")
        vbox.pack_start(self.if_name_label, True, True, 0)

        self.if_name_entry = Gtk.Entry()
        vbox.pack_start(self.if_name_entry, True, True, 0)

        self.con_name_label = Gtk.Label(label="Connection Name:")
        vbox.pack_start(self.con_name_label, True, True, 0)

        self.con_name_entry = Gtk.Entry()
        vbox.pack_start(self.con_name_entry, True, True, 0)

        self.passwd_label = Gtk.Label(label="Password:")
        vbox.pack_start(self.passwd_label, True, True, 0)

        self.passwd_entry = Gtk.Entry()
        self.passwd_entry.set_visibility(False)
        vbox.pack_start(self.passwd_entry, True, True, 0)

        self.create_button = Gtk.Button(label="Create Hotspot")
        self.create_button.connect("clicked", self.on_button_clicked)
        vbox.pack_start(self.create_button, True, True, 0)

    def on_button_clicked(self, widget):
        print("Create button clicked")
