========================
Guake 3! README file 85%
========================

|travis-badge|_ |bountysource-badge|_ |feathub-badge|_

.. |travis-badge| image:: https://travis-ci.org/Guake/guake.svg?branch=master
.. _travis-badge: https://travis-ci.org/Guake/guake

.. |bountysource-badge| image:: https://img.shields.io/bountysource/team/guake/activity.svg
.. _bountysource-badge: https://www.bountysource.com/teams/guake

.. |feathub-badge| image:: http://feathub.com/Guake/guake?format=svg
.. _feathub-badge: http://feathub.com/Guake/guake

Guake 0.8.x
-----------

Guake is under a big rework to port to Gtk3 branch. Stable release are available on the `0.8.x`
branch on this project

Introduction
~~~~~~~~~~~~

Guake is a dropdown terminal made fPor the GNOME desktop environment. Guake's style of window is
based on an FPS game, and one of its goals is to be easy to reach.

Guake is mostly written in Python and has a little piece in C (https://github.com/engla/keybinder).
The source code is placed in the ``guake`` directory. Files and images are in the ``data``
directory. Translation files are in the ``po`` directory.

What is this?
-------------

This is 3!, a port of Guake to use python3, Gtk3 and Vte 2.91!


TODO
----

- port all cli options
- - --version
- - --show ✓
- - --hide ✓
- - -f ✓
- - -t ✓
- - -p ✓
- - -a ✓
- - -n ✓
- - -s ✓
- - -g ✓
- - -l ✓
- - -e ✓
- - -i ✓
- - --bgimg (this option is removed from vte)
- - --bgcolor ✓
- - --fgcolor ✓
- - --rename-tab ✓
- - -r ✓
- - --rename-current-tab ✓
- - -q ✓
- - -u

- port dbus ✓ (after testing it with QDBusViewer it looks good)
- port the context menu of the terminal ✓
- - show ✓
- - click actions ✓
- - - copy ✓
- - - paste ✓
- - - toggle fullscreen ✓
- - - save to file ✓
- - - reset terminal ✓
- - - new tab ✓
- - - close tab ✓
- - - rename terminal ✓
- - - preferences ✓
- - - about✓
- - - quit ✓
- port the context menu of the tab bar ✓
- - show ✓
- - click actions ✓
- port the context menu of the tray icon v
- - show ✓
- - click actions ✓
- - - preferences ✓
- - - about ✓
- - - quit ✓
- port the scrollbar of the terminal ✓
- port the resizer ✓
- fix ctrl+d on terminal ✓
- fix double click on the tab bar ✓
- fix double click on tab to rename ✓
- fix clipboard from context menu ✓

- port the notification module ✓
- port the keyboard shortcuts ✓
- - ...
- port the pref screen ✓
- port gconfhandler to  gsettingshandler ✓
- - ...
- port about screen ✓
- port pattern matching ✓
- port Guake.accel* methods ✓
- add more stuff to this list
- port make stuff
- port install stuff
- update readme
- ...
- FIX all #TODO PORT sections
- Things to fix after the port
- - Rename widgets (from _ to -) to match the names used in the settings
- - Split files in to single class modules
- - fix tab bar buttons sometimes losing their text (eg after adding 3+ new tabs from the context menu, hovering them
restores the text) (I think this is a problem with the deprecated widgets which are still in use)
- - update the glade files (remove deprecated objects)
- - Simplify the color setting logic by removing the possibility to override the color buttons which are overriding the
    color palette (too much overrides...) ✓


There is stil lots of work to do. The first commit on this branch only gets guake up with one tab open.


Dev Tools
---------
- run guake3 from a terminal "./dev-gtk3.sh; kill %" this is needed since sig handler are not yet setup
- rebuild the gsettings schema "glib-compile-schemas data-gtk3/"

Dropped Features from Guake 0.8.x
---------------------------------

- --bgimg (this option is removed from vte)

New Deps
--------

- `libkeybinder3`

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

Execute the following command to bootstrap all needed system dependencies:

    $ ./bootstrap-ubuntu.sh


**Note**:

    Use the following commands to start guake without installing it:

        $ make dev
        $ make run

Testing as an unprivileged user
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run Guake as an unprivileged user for testing purposes, after `make` continue with::

    $ make run


System-wide installation
~~~~~~~~~~~~~~~~~~~~~~~~

TBD

Update translation
------------------

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

    $ make style
    $ make check

Update NEWS
-----------

Add your change in the ``NEWS`` file. The ``ChangeLog`` files is not used (PBR automatically
populates it for Pypi packages)

Versionning
-----------

Versioning is automatically done using git tags (thanks PBR).

Travis build
------------

Travis automatically check pull requests are compiling and check for code style.

Status of the master branch: https://travis-ci.org/Guake/guake.png?branch=master
