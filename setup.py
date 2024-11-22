#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os, subprocess


def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs(
                "{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True
            )
            mo_file = "{}/{}/LC_MESSAGES/{}".format(
                podir, po.split(".po")[0], "pardus-hotspot.mo"
            )
            msgfmt_cmd = "msgfmt {} -o {}".format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(
                (
                    "/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                    ["po/" + po.split(".po")[0] + "/LC_MESSAGES/pardus-hotspot.mo"],
                )
            )
    return mo


changelog = "debian/changelog"
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = "0.0.0"
    f = open("src/__version__", "w")
    f.write(version)
    f.close()

data_files = [
    ("/usr/bin", ["pardus-hotspot"]),
    ("/usr/share/applications", ["data/tr.org.pardus.hotspot.desktop"]),
    ("/usr/share/pardus/pardus-hotspot/ui", ["ui/MainWindow.glade"]),
    (
        "/usr/share/pardus/pardus-hotspot/src",
        [
            "src/Main.py",
            "src/MainWindow.py",
            "src/hotspot.py",
            "src/network_utils.py",
            "src/hotspot_settings.py",
            "src/__version__",
        ],
    ),
    ("/usr/share/pardus/pardus-hotspot/data",
        ["data/tr.org.pardus.hotspot-autostart.desktop",
         "data/pardus-hotspot.svg"
        ]
    ),
    ("/usr/share/icons/hicolor/scalable/apps/",
        ["data/pardus-hotspot.svg"]
    )
] + create_mo_files()


setup(
    name="pardus-hotspot",
    version=version,
    packages=find_packages(),
    scripts=["pardus-hotspot"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Emel Öztürk",
    author_email="emel.ozturk@pardus.org.tr",
    description="Simple hotspot application",
    license="GPLv3",
    keywords="pardus-hotspot, hotspot",
    url="https://github.com/pardus/pardus-hotspot",
)
