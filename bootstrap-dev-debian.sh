#!/bin/bash

echo "Install needed development packages on a Debian/Ubuntu system"

sudo apt install -y \
    aspell-fr \
    dconf-editor \
    gettext \
    gir1.2-keybinder-3.0 \
    gir1.2-vte-2.91 \
    gir1.2-notify-0.7 \
    glade \
    gsettings-desktop-schemas \
    libkeybinder-3.0-0 \
    make \
    pandoc \
    python3 \
    python3-gi \
    python3-pip \
    python3-cairo \
    libutempter0 \
    gnome-tweak-tool \

if [[ $1 == "--with-optional" ]]; then

    sudo apt install -y \
        numix-gtk-theme \

fi
