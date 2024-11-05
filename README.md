[🇹🇷](./README_TR.md) [🇬🇧](./README.md)

# Pardus Hotspot

## Introduction
This application is designed for Linux systems, providing a straightforward way
for users to effortlessly create and manage a Wi-Fi hotspot.
Featuring a graphical interface, it facilitates the configuration and management
of network settings with ease.


## Installation

### Requirements
Before installing Pardus Hotspot, ensure your system meets the following requirements:

- `network-manager`: The application relies on NetworkManager for managing network connections.
- `python3`: Pardus Hotspot is built with Python 3; make sure Python 3.x is installed on your system.
- `python3-dbus`: Required for the application to interact with NetworkManager.
- `libgtk-3-dev` & `libglib2.0-dev`: Required for the graphical interface.
- `gir1.2-ayatanaappindicator3-0.1`: Used for creating a system tray icon.
- `python3-gi`: Allows Python to use GTK and GNOME libraries.
- `gir1.2-gtk-3.0`: Provides the library for building windows and buttons.
- `gir1.2-gdkpixbuf-2.0`: Enables showing images, like QR codes.
- `python3-qrcode`: Used to create QR codes.
- `python3-pil` / `python3-pillow`: Helps handle images needed for QR codes.

### Usage
- Clone the repository and navigate to the cloned directory:

    ```
    git clone https://git.pardus.net.tr/emel.ozturk/pardus-hotspot.git
    cd pardus-hotspot
    ```

- Start the application:
    ```
    python3 Main.py
    ```

### Interface

When the hotspot is not active:

<img src="screenshots/disable.png" alt="Hotspot Disabled" width="500" height="auto"/>

When the hotspot is active:

<img src="screenshots/enable.png" alt="Hotspot Enabled" width="500" height="auto"/>

Settings configuration:

<img src="screenshots/settings.png" alt="Hotspot Settings" width="500" height="auto"/>


## Developer Notes
`MainWindow.py` acts as the entry point of the application. It utilizes
`hotspot.py` for the underlying logic to interact with the system's network
management.
`network_utils.py` is used for operations such as listing the available Wi-Fi
cards in the computer and getting the Wi-Fi's status.
`hotspot_settings.py:` handles configuration persistence and autostart
functionality.

___
## To-Dos
- [x] Implement dynamic retrieval of network interfaces
- [x] Stack page for important errors
- [x] Add support for different encryption methods
- [x] Improve error handling and user feedback
- [x] Check if the Wi-Fi is on or off
- [x] Enable connection for iPhones
- [x] Automatically disable connection if Wi-Fi signal lost
- [x] Remove connection if user wants to close hotspot
  window
- [x] Disable fullscreen mode
- [x] Fix freezing issue when switching between the about and settings buttons.
- [x] Add 'launch at startup' option
- [ ] Check if app is working on a virtual machine
- [ ] Check how many devices are connected to the hotspot
- [ ] Show connected device infos
- [ ] Add hidden parameter to show hotspot connection or not (only specific
  devices allowed)
- [x] ADD QR feature
- [ ] Change icons & tray icon


 __NOTE :__ When adding the application to GitHub, delete the __To-Dos__ section
 and update the __URL__
