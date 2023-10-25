#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from MainWindow import HotspotApp

class HotspotApplication(Gtk.Application):
    
    def __init__(self):
        super().__init__(application_id="tr.org.pardus.hotspot")
    
    def do_activate(self):
        window = HotspotApp(self)
        window.show_all()

if __name__ == "__main__":
    app = HotspotApplication()
    app.run(sys.argv)
