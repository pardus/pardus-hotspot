#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


if __name__ == "__main__":
    if run_forwarding_fix():
        sys.exit(0)
    else:
        sys.exit(1)
