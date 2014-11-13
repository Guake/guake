=================
Guake README file
=================

Introduction
~~~~~~~~~~~~

Guake is a dropdown terminal made for the GNOME desktop environment. Its style of window is based on
an fps games, and one of its goals is be easy to reach.

Guake is written mostly in python and has a little piece in C (global hotkeys stuff). The code is
placed in the src directory. Files and images are in the data directory. Translation stuff is in the
po directory.

Features? Bugs? Information?
----------------------------

Visit: http://guake.org/

Source Code available at: https://github.com/Guake/guake/


License
~~~~~~~

This program is free software; you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not,
write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
USA.


Dependencies
~~~~~~~~~~~~

 * Python2.7+
 * pygtk2.10 (gtk.StatusIcon)
 * python-vte
 * python-notify
 * python-dbus
 * python-gconf
 * python-xdg
 * python-appindicator (ubuntu)
 * notify-osd (ubuntu)
 * libutempter

To build guake, you will need the following packages too:

 * python-dev
 * gtk+-2.0-dev
 * pygtk-dev
 * gconf2-dev (to use some autoconf stuff)

For Python 3, you need this package too:

 * python3-dev

To edit the glade file, you can use the glade editor. Ensure to use the gtk-2 version:

 * glade-gtk2

Ubuntu
------

Under Debian/Ubuntu, make sure you have source code repositories enabled, then the following command
should install all the build dependencies::

    sudo apt-get build-dep guake

For compiling from these sources, please install the following packages (Ubuntu 13.10)::

    sudo apt-get install build-essential python autoconf
    sudo apt-get install gnome-common gtk-doc-tools libglib2.0-dev libgtk2.0-dev libgconf2-dev
    sudo apt-get install python-gtk2 python-gtk2-dev python-vte glade python-glade2 python-appindicator
    sudo apt-get install python-vte python-gconf
    sudo apt-get install notify-osd
    sudo apt-get install libutempter0
    # uncomment for Python 3
    # sudo apt-get install python3-dev
    # uncomment for glade Gtk-2 editor
    # sudo apt-get install glade-gtk2

RedHat/Fedora
-------------

For Fedora 19 and above, Guake is available in the official repositories and can be installed by
running::

    sudo yum install guake

For compiling from these sources, please install the following packages (Fedora 19)::

    TBD

ArchLinux
---------

Guake can be found in the `official repositories <https://www.archlinux.org/packages/?name=guake>`_
and installed by running::

    sudo pacman -S guake

For compiling from these sources, please install the following packages (TBD)::

    TBD

Compilation
~~~~~~~~~~~

We are using an autotools based installation, so if you got the source of guake from a release
tarball, please do the following::

    $ git clone https://github.com/Guake/guake.git
    $ cd guake
    $ ./autogen.sh && ./configure && make
    $ sudo make install

If you receive a message asking you if you have installed ``guake.schemas`` properly when launching
guake, it means that your default sysconfdir is different from the one chosen by autotools. To fix
that, you probably have to append the param ``--sysconfdir=/etc`` to your ``./configure`` call, like
this::

    $ ./configure --sysconfdir=/etc && make

If it is not enought you can install the gconf schemas file by hand by doing the following::

    # GCONF_CONFIG_SOURCE="" gconftool-2 --makefile-install-rule data/guake.schemas

For more install details, please read the ``INSTALL`` file.

Git hook
~~~~~~~~

Please install this git hook if you want to beautify your patch before submission::

    $ cd guake
    $ ln -s git-hooks/post-commit .git/hooks/
