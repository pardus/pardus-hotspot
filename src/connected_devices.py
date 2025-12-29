#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import re


class ConnectedDevices:

    STATION_RE = re.compile(r"Station\s+([0-9a-fA-F:]{17})")
    SIGNAL_RE = re.compile(r"signal:\s*(-?\d+)\s*dBm")
    IW_PATHS = ["/usr/sbin/iw", "/sbin/iw", "iw"]

    def __init__(self):
        self._interface = None

    def set_interface(self, interface):
        self._interface = interface

    def get_devices(self):
        """
        Returns list of dicts with keys: 'mac', 'ip', 'signal'
        """
        if not self._interface:
            return []

        stations = self._get_stations()
        if not stations:
            return []

        arp_table = self._get_arp_table()

        return [
            {
                "mac": mac.upper(),
                "ip": arp_table.get(mac.lower(), ""),
                "signal": signal
            }
            for mac, signal in stations.items()
        ]

    def _get_stations(self):
        iw_cmd = self._find_iw()
        if not iw_cmd:
            return {}

        try:
            result = subprocess.run(
                [iw_cmd, "dev", self._interface, "station", "dump"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False
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
        """
        Parse iw station dump output
        """
        stations = {}
        for block in re.split(r"(?=Station\s+[0-9a-fA-F:]{17})", output):
            mac_match = self.STATION_RE.search(block)
            if not mac_match:
                continue
            mac = mac_match.group(1)
            sig_match = self.SIGNAL_RE.search(block)
            stations[mac] = int(sig_match.group(1)) if sig_match else None
        return stations

    def _get_arp_table(self):
        """
        Read ARP table from /proc/net/arp for our interface
        """
        arp = {}
        try:
            with open("/proc/net/arp", "r") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 6 and parts[5] == self._interface:
                        mac = parts[3].lower()
                        if mac != "00:00:00:00:00:00":
                            arp[mac] = parts[0]
        except (OSError, IOError):
            pass
        return arp
