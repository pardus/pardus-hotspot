#!/usr/bin/python3

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk

from MainWindow import MainWindow

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="tr.org.pardus.pardus-hotspot", **kwargs)
        self.window = None
    
    def do_activate(self):
        self.window = MainWindow(self)


if __name__ == "__main__":
    app = Application()
    app.run(sys.argv)
