==============
Guake 3 README
==============

|travis-badge|_ |bountysource-badge|_ |feathub-badge|_

.. |travis-badge| image:: https://travis-ci.org/Guake/guake.svg?branch=master
.. _travis-badge: https://travis-ci.org/Guake/guake

.. |bountysource-badge| image:: https://img.shields.io/bountysource/team/guake/activity.svg
.. _bountysource-badge: https://www.bountysource.com/teams/guake

.. |feathub-badge| image:: http://feathub.com/Guake/guake?format=svg
.. _feathub-badge: http://feathub.com/Guake/guake

Introduction
============

Guake is a dropdown terminal made for the GNOME desktop environment. Guake's style of window is
based on an FPS game, and one of its goals is to be easy to reach.

Guake 3 Port
============

Guake has been ported Gtk3, thanks to the huge work of @aichingm.
Old releases and code depending on GTK2 have been put on the `0.8.x` branch and will no more be
actively maintained.


Here is the status of the port of Guake to Python3, Gtk3 and Vte 2.91:

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
- Rename widgets (from _ to -) to match the names used in the settings
- Split files in to single class modules
- fix tab bar buttons sometimes losing their text (eg after adding 3+ new tabs from the context
  menu, hovering them restores the text) (I think this is a problem with the deprecated widgets
  which are still in use)
- update the glade files (remove deprecated objects)
- Simplify the color setting logic by removing the possibility to override the color buttons which
  are overriding the color palette (too much overrides...) ✓


Dropped Features from Guake 0.8.x
---------------------------------

- `--bgimg` (this option is removed from vte)

New Dependencies
----------------

- `libkeybinder3`

Guake 3 Features
----------------

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
=======

This program is free software; you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not,
write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
USA.


System-wide installation
========================

Always use your package manager to install guake.

Ubuntu users will use `sudo apt install guake`.

If you really want to install Guake from source, use::

    $ make dev
    $ sudo make install-system

Note for maintainers
--------------------

Guake has drastically changed its build system with Guake 3. You may need to adapt all the
integration script accordingly.

Do not hesitate to contact me at `gaetan [at] xeberon.net`.


Development environment
=======================

Install System dependencies
---------------------------

Ubuntu
~~~~~~

Execute the following command to bootstrap all needed system dependencies::

    $ ./bootstrap-debian.sh

Setup development env
---------------------

Install the dependencies of your system and use the following commands::

    $ make dev
    $ make install-schemas  # still required even for local execution

Local execution of guake (without system-wide install)::

    $ make run

Git hook
~~~~~~~~

Please install this git hook if you want to beautify your patch before submission::

    $ make setup-githook

Validate your code
~~~~~~~~~~~~~~~~~~

We are strict on code styling, with pep8 and pylint running automatically in travis in
order to reject badly shaped patches. Please use the following command to validate all
python files::

    $ make style
    $ make check
    $ make test
    $ make build

Update translation
------------------

Update all translation files::

    $ make update-po

Install the translations files:
    $ sudo make install-locale

Then use your favorite po editor, such as ``poedit``.


Update NEWS
-----------

Add your change in the ``NEWS`` file. The ``ChangeLog`` files is not used (PBR automatically
populates it for Pypi packages)

Versionning
-----------

Versioning is automatically done using git tags. When a tag is pushed, a new version
is automatically created by PBR.

Travis build
------------

Travis automatically check pull requests are compiling and check for code style.

Status of the master branch: https://travis-ci.org/Guake/guake.png?branch=master
