#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from logging_config import get_logger

logger = get_logger()


def run_forwarding_fix():
    """
    Enable IP forwarding and add iptables FORWARD rule.
    - sysctl net.ipv4.ip_forward=1  (kernel forwarding)
    - iptables FORWARD ACCEPT        (idempotent: -C check before -I)
    """
    try:
        # Kernel IPv4 forwarding on
        subprocess.run(
            ["/usr/sbin/sysctl", "-w", "net.ipv4.ip_forward=1"],
            check=True, capture_output=True, text=True
        )

        # FORWARD ACCEPT rule
        chk = subprocess.run(
            ["iptables", "-C", "FORWARD", "-j", "ACCEPT"],
            check=False, capture_output=True, text=True
        )
        if chk.returncode != 0:
            subprocess.run(
                ["iptables", "-I", "FORWARD", "1", "-j", "ACCEPT"],
                check=True
            )

        logger.info("Forwarding configured (sysctl + iptables)")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to configure forwarding")
        logger.debug(f"Details: {e}")
        return False


def disconnect_station(interface, mac):
    iw_paths = ["/usr/sbin/iw", "/sbin/iw"]
    iw_cmd = None
    for path in iw_paths:
        if os.path.exists(path):
            iw_cmd = path
            break

    if not iw_cmd:
        logger.error("iw command not found")
        return False

    try:
        result = subprocess.run(
            [iw_cmd, "dev", interface, "station", "del", mac],
            capture_output=True, text=True, timeout=5, check=False
        )
        if result.returncode == 0:
            logger.info(f"Station {mac} disconnected from {interface}")
            return True
        logger.error(f"Failed to disconnect station {mac}: {result.stderr.strip()}")
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.error(f"Failed to disconnect station {mac}")
        logger.debug(f"Error details: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    action = sys.argv[1]

    if action == "forward":
        sys.exit(0 if run_forwarding_fix() else 1)
    elif action == "disconnect" and len(sys.argv) == 4:
        sys.exit(0 if disconnect_station(sys.argv[2], sys.argv[3]) else 1)
    else:
        sys.exit(1)
