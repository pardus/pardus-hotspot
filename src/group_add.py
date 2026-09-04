#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pwd
import re
import shutil
import subprocess
import sys

ALLOWED_GROUP = "netdev"
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.][a-zA-Z0-9_.-]*\$?$")


def add_to_group(user, group):
    adduser_path = shutil.which("adduser") or "/usr/sbin/adduser"
    if not os.path.isabs(adduser_path) or not os.path.exists(adduser_path):
        sys.stderr.write("Error: 'adduser' utility not found.\n")
        return 1

    res = subprocess.run([adduser_path, user, group], check=False)
    return res.returncode


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(f"Usage: {sys.argv[0]} <username> [{ALLOWED_GROUP}]\n")
        sys.exit(1)

    user = sys.argv[1]

    # Validate username
    if not USERNAME_REGEX.match(user) or len(user) > 32:
        sys.stderr.write(f"Error: Invalid username format '{user}'.\n")
        sys.exit(1)

    try:
        pwd.getpwnam(user)
    except KeyError:
        sys.stderr.write(f"Error: User '{user}' does not exist.\n")
        sys.exit(1)

    # Validate group (only 'netdev' is allowed)
    if len(sys.argv) > 2:
        group = sys.argv[2]
        if group != ALLOWED_GROUP:
            sys.stderr.write(
                f"Error: Unauthorized group '{group}'. Only '{ALLOWED_GROUP}' group is allowed.\n"
            )
            sys.exit(1)
    else:
        group = ALLOWED_GROUP

    rc = add_to_group(user, group)
    sys.exit(rc)


if __name__ == "__main__":
    main()

