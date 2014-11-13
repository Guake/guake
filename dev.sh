#!/bin/bash

# This script is used by the main developer to quickly compile and install the current version
# of Guake sources. Nothing say it will work directly on your environment. Use with caution!

if [[ ! -f configure ]]; then
    sudo apt-get install -y build-essential python autoconf
    sudo apt-get install -y gnome-common gtk-doc-tools libglib2.0-dev libgtk2.0-dev libgconf2-dev
    sudo apt-get install -y python-gtk2 python-gtk2-dev python-vte glade python-glade2
    sudo apt-get install -y python-vte python-gconf python-appindicator
    sudo apt-get install -y notify-osd libutempter0 glade-gtk2
    ./autogen.sh
fi

make && sudo make install && gconftool-2 --install-schema-file=/usr/local/etc/gconf/schemas/guake.schemas || exit 1

guake --quit 2> /dev/null
guake
