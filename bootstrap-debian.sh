#!/bin/bash

echo "Bootstraping required system packages for Guake (Debian/Ubuntu)"

sudo apt-get install -q \
    gir1.2-gtk-3.0 \
    gir1.2-keybinder \
    libgtk-3-0 \
    libgtk-3-dev \
    libkeybinder-3.0-0 \
    libvte-2.90-9 \
    python-dbus \
    python-dev \
    python-gi \
    python-gi-dev \
    python-gobject \
    python-keybinder \
    python3-dbus \
    python3-dev \
    python3-gi \
