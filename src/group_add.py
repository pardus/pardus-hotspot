#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys


def main():
    if len(sys.argv) > 2:
        rc = subprocess.call(["/usr/sbin/adduser", sys.argv[1], sys.argv[2]])
        sys.exit(rc)
    else:
        print("no argument passed")
        sys.exit(1)


if __name__ == "__main__":
    main()
