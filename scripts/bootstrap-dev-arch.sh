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
    sudo pacman -S \
		libwnck3 \
        libkeybinder3 \
        libnotify \
        python-cairo \
        python-dbus \
        python-gobject \
        python-pbr \
        vte3
fi

if [[ $MAKE == "1" ]]; then
    echo "Install packages needed for making guake"
    sudo pacman -S \
        gettext \
        gsettings-desktop-schemas \
        make \
        pandoc \
        python-pipenv
fi

if [[ $DEV == "1" ]]; then
    echo "Install needed development packages"
    sudo pacman -S \
        dconf-editor \
        glade \
        poedit \
        gnome-tweak-tool
fi

if [[ $OPT == "1" ]]; then
echo "Install packages optional for execution"
    sudo pacman -S \
        libutempter \
        numix-gtk-theme
fi
