#!/bin/bash

echo "Install packages needed for execution"

sudo apt install -y \
    gir1.2-keybinder-3.0 \
    gir1.2-notify-0.7 \
    gir1.2-vte-2.91 \
    libkeybinder-3.0-0 \
    python3 \
    python3-cairo \
    python3-dbus \
    python3-gi \
    python3-pbr \
    python3-pip \

echo "Install needed development packages on a Debian/Ubuntu system"
sudo apt install -y \
    aspell-fr \
    dconf-editor \
    gettext \
    glade \
    gnome-tweak-tool \
    gsettings-desktop-schemas \
    make \
    pandoc \

if [[ $1 == "--with-optional" ]]; then

    sudo apt install -y \
        libutempter0 \
        numix-gtk-theme \

fi
