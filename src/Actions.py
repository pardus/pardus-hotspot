#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from logging_config import get_logger

logger = get_logger()


def run_iptables_forward():
    """
    Add iptables forward rule to accept all forwarded traffic.
    """
    try:
        subprocess.run(["iptables", "-A", "FORWARD", "-j", "ACCEPT"], check=True)
        logger.info("Successfully configured iptables FORWARD rule")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to configure iptables FORWARD rule")
        logger.debug(f"iptables command error details: {e}")
        return False


if __name__ == "__main__":

    if run_iptables_forward():
        sys.exit(0)
    else:
        sys.exit(1)
