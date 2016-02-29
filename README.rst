=================
Guake README file
=================

|travis-badge|_

.. |travis-badge| image:: https://travis-ci.org/Guake/guake.png?branch=master
.. _travis-badge: https://travis-ci.org/Guake/guake

Introduction
~~~~~~~~~~~~

Guake is a dropdown terminal made for the GNOME desktop environment. Guake's style of window is based on
an FPS game, and one of its goals is to be easy to reach.

Guake is mostly written in Python and has a little piece in C (https://github.com/engla/keybinder). The source code is placed in the ``guake`` directory. Files and images are in the ``data`` directory. Translation files are in the ``po`` directory.

Features
--------

- Lightweight
- Simple Easy and Elegant
- Smooth integration of terminal into GUI
- Appears when you call and disappears once you are done by pressing a predefined hotkey (F12 by
  default)
- Compiz transparency support
- Multi tab
- Plenty of color palettes
- Quick Open in your favorite text editor with a click on a file name (with line number support)
- Customizable hotkeys for tab access, reorganization, background transparency, font size,...
- Extremely configurable
- Configure Guake startup by running a bash script when Guake starts
- Multi-monitor support (open on a specified monitor, open on mouse monitor)
- Save terminal content to file
- Open URL to your browser

Bugs? Information?
------------------

Source Code available at: https://github.com/Guake/guake/

Official Homepage: http://guake-project.org

**Important note**: Do **NOT** use the domain guake.org, it has been registered by someone outside
the team. We cannot be held responsible for the content on that web site.


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
 * notify-osd (ubuntu)
 * python-appindicator (ubuntu)
 * python-dbus
 * python-gconf
 * python-keybinder
 * python-notify
 * python-vte
 * python-xdg
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

To have beautiful color logs when you debug Guake, install colorlog, so you'll have great logs in
the terminal that launched Guake!

 * pip install colorlog

Installation
~~~~~~~~~~~~

Ubuntu
------

Execute the following command to install guake with all default options::

    $ ./dev.sh --install

It will install all dependencies, compiles and install all files to ``/usr/local``.

**Note**:

    Use the following command to start guake without installing it (you need to have installed it at
    least once)::

        $ ./dev.sh

PPA
***

An external, unofficial PPA for latest version of Ubuntu seems to integrate Guake regularly. Check
it at the following URL:

    https://launchpad.net/~webupd8team/+archive/ubuntu/unstable

Details:
********

Under Debian/Ubuntu, make sure you have source code repositories enabled, then the following command
should install all the build dependencies::

    sudo apt-get build-dep guake

For compiling from these sources, please install the following packages (Ubuntu 13.10)::

    sudo apt-get install build-essential python autoconf
    sudo apt-get install gnome-common gtk-doc-tools libglib2.0-dev libgtk2.0-dev
    sudo apt-get install python-gtk2 python-gtk2-dev python-vte glade python-glade2
    sudo apt-get install libgconf2-dev python-appindicator
    sudo apt-get install python-vte python-gconf python-keybinder
    sudo apt-get install notify-osd
    sudo apt-get install libutempter0
    sudo apt-get install python-notify
    # uncomment for Python 3
    # sudo apt-get install python3-dev
    # uncomment for glade Gtk-2 editor
    # sudo apt-get install glade-gtk2

RedHat/Fedora
-------------

For Fedora 19 and above, Guake is available in the official repositories and can be installed by
running::

    sudo yum install guake		# for Fedora 19 - 21
    sudo dnf install guake		# for Fedora 23 and above

For compiling from these sources, please install the following packages (Fedora 19)::

    TBD

ArchLinux
---------

Guake can be found in the `official repositories <https://www.archlinux.org/packages/?name=guake>`_
and installed by running::

    sudo pacman -S guake

For compiling from these sources, please install the following packages (for Python 2)::

    gnome-common python2-gconf python2-xdg
  
To run Guake with Python 2, use the trick described in `Arch Wiki <https://wiki.archlinux.org/index.php/Python#Dealing_with_version_problem_in_build_scripts>`_ and put this as your ``/usr/local/bin/python`` (changing ``/path/to/guake`` into a real path where you cloned the repository)::

    #!/bin/bash
    script=$(readlink -f -- "$1")
    case "$script" in (/path/to/guake*)
        exec python2 "$@"
        ;;
    esac
    
    exec python3 "$@"

Make it executable with ``chmod +x /usr/local/bin/python``.
  
  

Compilation
~~~~~~~~~~~

We are using an autotools based installation, so if you got the source of guake from a release
tarball, please do the following::

    $ git clone https://github.com/Guake/guake.git
    $ cd guake
    $ ./autogen.sh && ./configure && make

For Ubuntu user, we have a script that does all these steps for you. Use::

    $ ./dev.sh


Testing as an unprivileged user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run Guake as an unprivileged user for testing purposes, after `make` continue with::

    $ gconftool-2 --install-schema-file=data/guake.schemas
    $ PYTHONPATH=src python src/guake/main.py

**Note**: Ubuntu users, you can use the following command::

   $ ./dev.sh

System-wide installation
~~~~~~~~~~~~~~~~~~~~~~~~

To install Guake to all users, after `make` continue with::

    $ sudo make install

If you receive a message asking you if you have installed ``guake.schemas`` properly when launching
guake, it means that your default sysconfdir is different from the one chosen by autotools. To fix
that, you probably have to append the param ``--sysconfdir=/etc`` to your ``./configure`` call, like
this::

    $ ./configure --sysconfdir=/etc && make

If it is not enought you can install the gconf schemas file by hand by doing the following::

    $ GCONF_CONFIG_SOURCE="" gconftool-2 --makefile-install-rule data/guake.schemas

For more install details, please read the ``INSTALL`` file.

Development
~~~~~~~~~~~

Upate translation
-----------------

First update all translation files::

    $ cd po
    $ make update-po

Then use your favorite po editor, such as ``poedit``.

Once finished, compile your result with::

    $ cd po
    $ make

Git hook
--------

Please install this git hook if you want to beautify your patch before submission::

    $ cd guake
    $ ln -s git-hooks/post-commit .git/hooks/

Validate your code
------------------

We are strict on code styling, with pep8 and pylint running automatically in travis in
order to reject badly shaped patches. Please use the following command to validate all
python files::

    $ ./validate.sh

Update NEWS
-----------

Add your change in the ``NEWS`` file. The ``ChangeLog`` files is not more used.

New version
-----------

To start development on a new version:

- update ``configure.ac``::

    AC_INIT([guake], [0.x.y], [http://guake-project.org/])

- add a new section in the ``NEWS`` file

When read, create a new release on the github site.

Travis build
------------

Travis automatically check pull requests are compiling and check for code style.

Status of the master branch: https://travis-ci.org/Guake/guake.png?branch=master
