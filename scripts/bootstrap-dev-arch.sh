#!/bin/bash

echo "Install packages needed for execution"
sudo pacman -S \
    libkeybinder3 \
    libnotify \
    libutempter \
    python-cairo \
    python-dbus \
    python-gobject \
    python-pbr \
    vte3 \
