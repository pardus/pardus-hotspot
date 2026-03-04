#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import threading
import time
import logging

log = logging.getLogger(__name__)

IPTABLES = "/usr/sbin/iptables"
WPA_CLI = "/sbin/wpa_cli"
WPA_SOCKET = "/run/wpa_supplicant"
BLOCKED_MACS_FILE = "/var/lib/hotspot_blocked_macs"


class ConnectedDevices:

    STATION_RE = re.compile(r"Station\s+([0-9a-fA-F:]{17})")
    SIGNAL_RE = re.compile(r"signal:\s*(-?\d+)")
    CONNECTED_TIME_RE = re.compile(r"connected time:\s*(\d+)\s*seconds")
    IW_PATHS = ["/usr/sbin/iw", "/sbin/iw", "iw"]

    def __init__(self):
        self._interface = None

    def set_interface(self, interface):
        self._interface = interface

    def get_devices(self):
        if not self._interface:
            return []

        stations = self._get_stations()
        if not stations:
            return []

        arp_table = self._get_arp_table()
        blocked = self._get_blocked_macs()

        devices = []
        for mac, info in stations.items():
            if mac.lower() in blocked:
                continue
            ip = arp_table.get(mac.lower(), "")
            hostname = self._resolve_hostname(ip) if ip else ""
            devices.append({
                "mac": mac.upper(),
                "ip": ip,
                "hostname": hostname,
                "signal": info["signal"],
                "time": info["time"],
                "blocked": False,
            })
        return devices

    # ------------------------------------------------------------------ #
    #  Block / Unblock                                                     #
    # ------------------------------------------------------------------ #

    def block_device(self, mac: str) -> bool:
        mac = mac.lower()
        if not self._iptables_add(mac):
            return False
        self._ebtables_add(mac)
        ip = self._ip_for_mac(mac)
        if ip:
            self._conntrack_flush(ip)
            self._arp_delete(ip)
        self._wpa_deauth_loop(mac)
        self._persist_add(mac)
        return True

    def unblock_device(self, mac: str) -> bool:
        mac = mac.lower()
        self._iptables_remove(mac)
        self._ebtables_remove(mac)
        self._persist_remove(mac)
        return True

    def _get_blocked_macs(self) -> set:
        blocked = set()
        try:
            result = subprocess.run(
                [IPTABLES, "-L", "INPUT", "-n"],
                capture_output=True, text=True, timeout=3
            )
            mac_re = re.compile(r"MAC ([0-9a-fA-F:]{17})", re.IGNORECASE)
            for m in mac_re.finditer(result.stdout):
                blocked.add(m.group(1).lower())
        except Exception as e:
            log.error("iptables list error: %s", e)
        return blocked

    def _iptables_add(self, mac: str) -> bool:
        if mac in self._get_blocked_macs():
            return True
        try:
            for chain in ("INPUT", "FORWARD"):
                subprocess.run(
                    [IPTABLES, "-I", chain, "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                    capture_output=True, text=True, check=True, timeout=5
                )
            return True
        except subprocess.CalledProcessError as e:
            log.error("iptables add failed for %s: %s", mac, e.stderr)
            return False

    def _iptables_remove(self, mac: str):
        for chain in ("INPUT", "FORWARD"):
            for _ in range(5):
                r = subprocess.run(
                    [IPTABLES, "-D", chain, "-m", "mac", "--mac-source", mac, "-j", "DROP"],
                    capture_output=True, text=True
                )
                if r.returncode != 0:
                    break

    def _ebtables_add(self, mac: str):
        for chain in ("INPUT", "FORWARD"):
            subprocess.run(["ebtables", "-I", chain, "-s", mac, "-j", "DROP"], capture_output=True)

    def _ebtables_remove(self, mac: str):
        for chain in ("INPUT", "FORWARD"):
            subprocess.run(["ebtables", "-D", chain, "-s", mac, "-j", "DROP"], capture_output=True)

    def _conntrack_flush(self, ip: str):
        try:
            subprocess.run(["conntrack", "-D", "-s", ip], capture_output=True)
            subprocess.run(["conntrack", "-D", "-d", ip], capture_output=True)
        except FileNotFoundError:
            pass

    def _arp_delete(self, ip: str):
        if not self._interface:
            return
        subprocess.run(
            ["ip", "neigh", "del", ip, "dev", self._interface],
            capture_output=True
        )

    def _ip_for_mac(self, mac: str) -> str:
        arp = self._get_arp_table()
        return arp.get(mac.lower(), "")

    def _wpa_deauth_loop(self, mac: str, count: int = 10):
        iface = self._interface

        def _loop():
            for _ in range(count):
                subprocess.run(
                    [WPA_CLI, "-i", iface, "-p", WPA_SOCKET, "deauthenticate", mac],
                    capture_output=True
                )
                subprocess.run(
                    [WPA_CLI, "-i", iface, "-p", WPA_SOCKET, "disassociate", mac],
                    capture_output=True
                )
                subprocess.run(
                    ["iw", "dev", iface, "station", "del", mac],
                    capture_output=True
                )
                time.sleep(0.2)

        threading.Thread(target=_loop, daemon=True).start()

    def _persist_add(self, mac: str):
        macs = self._load_persisted()
        macs.add(mac)
        self._save_persisted(macs)

    def _persist_remove(self, mac: str):
        macs = self._load_persisted()
        macs.discard(mac)
        self._save_persisted(macs)

    def _load_persisted(self) -> set:
        if not os.path.exists(BLOCKED_MACS_FILE):
            return set()
        try:
            with open(BLOCKED_MACS_FILE) as f:
                return {l.strip().lower() for l in f if l.strip()}
        except OSError:
            return set()

    def _save_persisted(self, macs: set):
        try:
            with open(BLOCKED_MACS_FILE, "w") as f:
                f.writelines(f"{m}\n" for m in sorted(macs))
        except OSError as e:
            log.error("Failed to save blocked MACs: %s", e)

    # ------------------------------------------------------------------ #
    #  Station / ARP helpers                                              #
    # ------------------------------------------------------------------ #

    def _get_stations(self):
        iw_cmd = self._find_iw()
        if not iw_cmd:
            return {}
        try:
            result = subprocess.run(
                [iw_cmd, "dev", self._interface, "station", "dump"],
                capture_output=True, text=True, timeout=3, check=False
            )
            if result.returncode != 0:
                return {}
            return self._parse_stations(result.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return {}

    def _find_iw(self):
        for path in self.IW_PATHS:
            if path == "iw" or os.path.exists(path):
                return path
        return None

    def _parse_stations(self, output):
        stations = {}
        for block in re.split(r"(?=Station\s+[0-9a-fA-F:]{17})", output):
            mac_match = self.STATION_RE.search(block)
            if not mac_match:
                continue
            mac = mac_match.group(1)
            sig_match = self.SIGNAL_RE.search(block)
            time_match = self.CONNECTED_TIME_RE.search(block)
            stations[mac] = {
                "signal": int(sig_match.group(1)) if sig_match else None,
                "time": int(time_match.group(1)) if time_match else None,
            }
        return stations

    def _get_arp_table(self):
        arp = {}
        try:
            with open("/proc/net/arp") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 6 and parts[5] == self._interface:
                        mac = parts[3].lower()
                        if mac != "00:00:00:00:00:00":
                            arp[mac] = parts[0]
        except OSError:
            pass
        return arp
    def _resolve_hostname(self, ip: str) -> str:
        lease_file = f"/var/lib/NetworkManager/dnsmasq-{self._interface}.leases"
        try:
            with open(lease_file) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[2] == ip:
                        name = parts[3]
                        if name and name != "*":
                            return name
        except OSError:
            pass
        try:
            import socket
            name = socket.gethostbyaddr(ip)[0]
            if name and name != ip:
                return name.split(".")[0]
        except Exception:
            pass
        return ""
