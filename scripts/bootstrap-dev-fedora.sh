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
    sudo yum install \
        python3-devel \
        python3-cairo \
        python3-dbus \
        python3-pip \
        keybinder3 \
		libwnck
fi

if [[ $MAKE == "1" ]]; then
    echo "Install packages needed for making guake"
    sudo yum install \
        gettext \
        gsettings-desktop-schemas \
        make \
        pandoc
fi

if [[ $DEV == "1" ]]; then
    echo "Install needed development packages"
    sudo yum install \
        dconf-editor \
        glade \
        poedit \
        gnome-tweak-tool
fi

if [[ $OPT == "1" ]]; then
    echo "Install packages optional for execution"
    sudo yum install \
        libutempter \
        numix-gtk-theme
fi
