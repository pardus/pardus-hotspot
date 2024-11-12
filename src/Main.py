#!/usr/bin/python3

import sys
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk

from MainWindow import MainWindow

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="tr.org.pardus.pardus-hotspot",
                         flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs
        )
        self.window = None
        GLib.set_prgname("tr.org.pardus.pardus-hotspot")

        self.add_main_option(
            "tray",
            ord("t"),
            GLib.OptionFlags(0),
            GLib.OptionArg(0),
            "Start application on tray mode",
            None,
        )


    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            self.window = MainWindow(self)
        else:
            self.window.present()


    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()
        self.args = options
        self.activate()
        return 0

# Application instance is created and run here directly without checking __name__
app = Application()
app.run(sys.argv)
