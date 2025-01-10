from configparser import ConfigParser
from pathlib import Path
import os


class HotspotSettings:
    def __init__(self):
        self.user_home = str(Path.home())
        self.config_dir = os.path.join(
            self.user_home,
            ".config",
            "pardus",
            "pardus-hotspot"
        )
        self.autostartdir = os.path.join(
            self.user_home,
            ".config",
            "autostart"
        )
        self.config_file = "settings.ini"
        self.config = ConfigParser(strict=False)

        self.autostart_file = "pardus-hotspot-autostart.desktop"

        self.default_ssid = ''
        self.default_password = ''
        self.default_interface = ''
        self.default_encryption = ''
        self.default_autostart = False
        self.default_band = '2.4GHz'
        self.default_forwarding = False

        self.ssid = self.default_ssid
        self.password = self.default_password
        self.interface = self.default_interface
        self.encryption = self.default_encryption
        self.autostart = self.default_autostart
        self.band = self.default_band
        self.forwarding = self.default_forwarding


    def create_default_config(self, force=False):
        self.config['Hotspot'] = {
            "ssid": self.ssid,
            "password": self.password,
            "interface": self.interface,
            "encryption": self.encryption,
            "autostart": str(self.autostart),
            "band": self.band,
            "forwarding": str(self.forwarding)
        }

        config_path = os.path.join(self.config_dir, self.config_file)
        if not Path(config_path).is_file() or force:
            self.create_dir(self.config_dir)
            with open(config_path, "w") as configfile:
                self.config.write(configfile)


    def read_config(self):
        config_path = os.path.join(self.config_dir, self.config_file)
        try:
            self.config.read(config_path)
            self.ssid = self.config.get(
                'Hotspot', 'ssid', fallback=self.default_ssid
            )
            self.password = self.config.get(
                'Hotspot', 'password', fallback=self.default_password
            )
            self.interface = self.config.get(
                'Hotspot', 'interface', fallback=self.default_interface
            )
            self.encryption = self.config.get(
                'Hotspot', 'encryption', fallback=self.default_encryption
            )
            self.autostart = self.config.getboolean(
                'Hotspot', 'autostart', fallback=self.default_autostart
            )
            self.band = self.config.get(
                'Hotspot', 'band', fallback=self.default_band
            )
            self.forwarding = self.config.getboolean(
                'Hotspot', 'forwarding', fallback=self.default_forwarding
            )
        except Exception as e:
            print(f"Error reading configuration: {e}")
            self.create_default_config(force=True)


    def write_config(self):
        self.config['Hotspot'] = {
            "ssid": self.ssid,
            "password": self.password,
            "interface": self.interface,
            "encryption": self.encryption,
            "autostart": self.autostart,
            "band": self.band,
            "forwarding": str(self.forwarding)
        }

        if self.create_dir(self.config_dir):
            with open(
                os.path.join(self.config_dir, self.config_file), "w"
            ) as configfile:
                self.config.write(configfile)
                return True
        return False


    def create_dir(self, dir_path):
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}")
            return False


    def set_autostart(self, state):
        try:
            os.makedirs(self.autostartdir, exist_ok=True)
        except OSError as e:
            print(f"Error creating directory {self.autostartdir}: {e}")
            return

        autostart_file_path = os.path.join(self.autostartdir, self.autostart_file)
        target_desktop_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../data/tr.org.pardus.hotspot-autostart.desktop"
        )

        if state:
            if not os.path.exists(target_desktop_file):
                print(f"Target desktop file does not exist: {target_desktop_file}")
                return

            # Create the symlink
            if not os.path.exists(autostart_file_path):
                try:
                    os.symlink(target_desktop_file, autostart_file_path)
                except OSError as e:
                    print(f"Error creating symlink: {e}")
            else:
                print("Autostart symlink already exists")
        else:
            # Remove the symlink
            if os.path.exists(autostart_file_path):
                try:
                    os.unlink(autostart_file_path)
                except OSError as e:
                    print(f"Error removing autostart symlink: {e}")

        # Update the autostart setting and write to config
        self.autostart = state
        self.write_config()
