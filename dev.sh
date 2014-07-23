#!/bin/sh

# This script is used by the main developer to quickly compile and install the current version
# of Guake sources. Nothing say it will work directly on your environment. Use with caution!

[ ! -f configure ] && ./autogen.sh

make && sudo make install && gconftool-2 --install-schema-file=/usr/local/etc/gconf/schemas/guake.schemas || exit 1

guake --quit 2> /dev/null
guake
