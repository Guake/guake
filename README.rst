==============
Guake 3 README
==============

|travis-badge|_

.. |travis-badge| image:: https://travis-ci.org/Guake/guake.svg?branch=guake3
.. _travis-badge: https://travis-ci.org/Guake/guake


Introduction
============

Guake is a dropdown terminal made for the GNOME desktop environment. Guake's style of window is
based on a famous FPS game, and one of its goals is to be easy to reach with a single key stroke at
any given point in your day.

Guake is mostly written in Python 3.

Features
--------

- Lightweight
- Tight integration in GNOME desktop
- Simple, Easy and Elegant
- Appears when you call and disappears once you are done by pressing a predefined hotkey (F12 by
  default)
- Compiz transparency support
- Multi tab
- Plenty of color palettes
- Quick Open a filename printed in the console in your favorite text editor
- Customizable hotkeys for tab access, reorganization, background transparency, font size,...
- Multi-monitor support
- Save terminal content to file
- Open URL to your browser

Bugs? Information?
------------------

Source Code available at: https://github.com/Guake/guake/

Official Homepage: http://guake-project.org

**Important note**: Do **NOT** use the domain guake.org, it has been registered by someone outside
the team. We cannot be held responsible for the content on that web site.


License
-------

This program is free software; you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not,
write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
USA.

Installation
============

Guake can be installed by 3 different methods:

- **development**: ideal for hacks and development. It creates a virtual environment directly within
  the Guake source tree. Note that you cannot use the `guake` command directly, you will need to
  **activate** the virtualenv first.
- **system**: install Guake on your system still using a virtual environment. The `guake` command
  will be accessible directly, you will have all the icon and system change applied.
- **distrib**: installation of Guake, packaged, and prepared by your Linux Distribution, it may not
  use virtualenv. This is the prefered way of installing Guake for end user. Just use your package
  manager (`apt` or `aptitude` on Debian/Ubuntu)

Setting up a Development environment
------------------------------------

First, you need to install some system libraries, mainly GTK and related.

- On Ubuntu and Debian, use:

    $ ./bootstrap-debian.sh

Now, install Guake inside a new virtualenv with:

    $ ./install.py

This script will use the Python executable of your system to create a bootstrap a clean virtualenv
where Guake will be installed. To use Guake afterward, do not forget to activate the virtualenv:

    $ source activate
    $ guake

You can also execute all checks and unit test directly after the installation using:

    $ ./install.py --checks --tests


Unit test can be executed directly with:

    $ python setup.py test


Setup on your system
--------------------

    $ ./install.py --target=system

Note: **not supported yet**.


Distrib setup
-------------

Using this source tree to install Guake directly on your system directly is a **wrong** idea. It
should always be installed in a proper virtualenv, to avoid messing with your system's Python
modules. Of course, Guake relies on VTE and GTK modules that shall come from your system, but there
is no reason to let Guake override any python package of your system.

In a more general maner, **never install a Python package in you system**. Always use a Virtualenv.

To install Guake, use the packaged version in your distribution (Ubuntu, Debian, Fedora,...), it
will probably not use virtualenv **but** the Python package versions coherency is checked by your
distribution validation campaign.

However, please see:
    https://hynek.me/articles/python-deployment-anti-patterns/
