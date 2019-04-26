#!/bin/bash

RUN=0
MAKE=0
DEV=0
OPT=0
ARGC="$#"

while test $# -gt 0
do
    case "$1" in
        run)
          RUN=1
          ;;
        make)
          MAKE=1
          ;;
        dev)
          DEV=1
          ;;
        opt)
          OPT=1
          ;;
    esac
    shift
done

if [[ "$ARGC" == "0" ]]; then
          RUN=1;
          MAKE=1;
          DEV=1;
          OPT=0;
fi


if [[ $RUN == "1" ]]; then
    echo "Install packages needed for execution"
    sudo apt install -y \
        gir1.2-keybinder-3.0 \
        gir1.2-notify-0.7 \
        gir1.2-vte-2.91 \
		gir1.2-wnck-3.0 \
        libkeybinder-3.0-0 \
        libutempter0 \
        python3 \
        python3-cairo \
        python3-dbus \
        python3-gi \
        python3-pbr \
        python3-pip
fi

if [[ $MAKE == "1" ]]; then
    echo "Install packages needed for making guake"
    sudo apt install -y \
        gettext \
        gsettings-desktop-schemas \
        make \
        pandoc
fi

if [[ $DEV == "1" ]]; then
    echo "Install needed development packages"
    sudo apt install -y \
        aspell-fr \
        colortest \
        dconf-editor \
        glade \
        poedit \
        gnome-tweak-tool
fi

if [[ $OPT == "1" ]]; then
    echo "Install packages optional for execution"
    sudo apt install -y \
        numix-gtk-theme
fi
