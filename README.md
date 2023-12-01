# Pardus Hotspot Application

## Introduction
This application is designed for Linux systems, providing a straightforward way for users to effortlessly create and manage a Wi-Fi hotspot. Featuring a graphical interface, it facilitates the configuration and management of network settings with ease.

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
`MainWindow.py` acts as the entry point of the application. It utilizes `hotspot.py` for the underlying logic to interact with the system's network management.

## To-Dos
- [ ] Implement dynamic retrieval of network interfaces.
- [ ] Add support for different encryption methods.
- [ ] Introduce a feature to save and load preset configurations.
- [ ] Improve error handling and user feedback.
