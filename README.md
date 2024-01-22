
[🇹🇷](./README_TR.md) [🇬🇧](./README.md)

# Pardus Hotspot Application

## Introduction
This application is designed for Linux systems, providing a straightforward way
for users to effortlessly create and manage a Wi-Fi hotspot.
Featuring a graphical interface, it facilitates the configuration and management of network settings with ease.

## Installation

### Prerequisites
- Ensure you have NetworkManager and Python 3.x installed on your system.
- D-Bus Python bindings are required for the application to interact with NetworkManager.

### Usage
- Clone the repository:

    ```
    git clone https://git.pardus.net.tr/emel.ozturk/pardus-hotspot-app.git
    ```

- To start the application, run:
    `python3 Main.py`

### Interface

When the hotspot is not active:

<img src="img/disable.png" alt="Hotspot Disabled" width="500" height="auto"/>

When the hotspot is active:

<img src="img/enable.png" alt="Hotspot Enabled" width="500" height="auto"/>

Settings configuration:

<img src="img/settings.png" alt="Hotspot Settings" width="500" height="auto"/>

### Hotspot Configuration
- The interface allows for setting the SSID, connection name, password, and other network-related configurations.

## Developer Notes
`MainWindow.py` acts as the entry point of the application. It utilizes
`hotspot.py` for the underlying logic to interact with the system's network
management.
`network_utils.py` is used for operations such as listing the available Wi-Fi
cards in the computer and getting the Wi-Fi's status.

## To-Dos
- [x] Implement dynamic retrieval of network interfaces
- [x] Stack page for important errors
- [x] Add support for different encryption methods
- [x] Improve error handling and user feedback
- [ ] Check if app is working on a virtual machine
- [x] Check if the Wi-Fi is on or off
- [x] Enable connection for iPhones
- [x] Automatically disable connection if Wi-Fi signal lost
- [x] Remove connection if user wants to close hotspot manager
  window
- [x] Disable fullscreen mode
- [x] Fix freezing issue when switching between the about and settings buttons.
- [ ] Check how many devices are connected to the hotspot
- [ ] Show connected device infos
- [ ] Add hidden parameter to show hotspot connection or not (only specific
  devices allowed)
- [ ] ADD QR feature


 __NOTE :__ When adding the application to GitHub, delete the __To-Dos__ section
 and update the __URL__
