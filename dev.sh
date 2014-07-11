#!/bin/sh

[ ! -f configure ] && ./autogen.sh

make && sudo make install && gconftool-2 --install-schema-file=/usr/local/etc/gconf/schemas/guake.schemas || exit 1

guake --quit 2> /dev/null
guake
