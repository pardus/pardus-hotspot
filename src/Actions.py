#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys

def run_iptables_forward():
    """
    Add iptables forward rule to accept all forwarded traffic.
    """
    try:
        subprocess.run(["iptables", "-A", "FORWARD", "-j", "ACCEPT"], check=True)
        print("Successfully added FORWARD rule.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to add FORWARD rule: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":

    if run_iptables_forward():
        sys.exit(0)
    else:
        sys.exit(1)
