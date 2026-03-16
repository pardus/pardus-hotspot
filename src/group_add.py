#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys


def main():
    def add_to_group(user, group):
        subprocess.call(["adduser", user, group])

    if len(sys.argv) > 2:
        add_to_group(sys.argv[1], sys.argv[2])
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
