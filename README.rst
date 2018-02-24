==============
Guake 3 README
==============

|travis-badge|_ |bountysource-badge|_

.. |travis-badge| image:: https://travis-ci.org/Guake/guake.svg?branch=master
.. _travis-badge: https://travis-ci.org/Guake/guake

.. |bountysource-badge| image:: https://img.shields.io/bountysource/team/guake/activity.svg
.. _bountysource-badge: https://www.bountysource.com/teams/guake


Introduction
============

Guake is a dropdown terminal made for the GNOME desktop environment. Guake's style of window is
based on an FPS game, and one of its goals is to be easy to reach.

Request Features
----------------

Please vote for feature on `FeatHub <http://feathub.com/Guake/guake>`_.
Open Issues on GitHub only for bug reports.

Most requested features list for Guake:

|feathub-badge|_

.. |feathub-badge| image:: http://feathub.com/Guake/guake?format=svg
.. _feathub-badge: http://feathub.com/Guake/guake


Guake 3 Port
============

Guake has recently been ported Gtk3, thanks to the huge work of @aichingm.
Old releases and code depending on GTK2 have been put on the
`0.8.x <https://github.com/Guake/guake/tree/0.8.x>`_ branch and will no more be actively maintained.

Please note that we target to support mainly the GTK and VTE versions found by default on most
popular distribution such as Ubuntu LTS (currently: Ubuntu 16.04 LTS and 17.10).

Guake has also been ported to Python 3.5+.

Dropped Features from Guake 0.8.x
---------------------------------

- ``--bgimg`` (this option has been removed from vte)

Dependencies
------------

Here are the dependencies of Guake for its execution:

- GTK: 3.18
- VTE: 2.91 (`vte-0.42 <https://packages.ubuntu.com/xenial/gir1.2-vte-2.91>`_)
- ``gir1.2-keybinder-3.0``
- ``gir1.2-notify-0.7``
- ``gir1.2-vte-2.91``
- ``libkeybinder3``
- ``python3-cairo``
- ``python3-dbus``
- ``python3-gi``
- ``python3-pbr``

Optional dependencies:

- ``libutempter0``
- ``numix-gtk-theme``

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

Always prefere using your package manager to install guake.

Ubuntu users will use `sudo apt install guake`.

If you really want to install Guake from these sources, use:

.. code-block:: bash

    $ make
    $ sudo make install

To uninstall, still in the source directory:

.. code-block:: bash

    $ make
    $ sudo make uninstall

Tips for a complete Guake reinstallation:

.. code-block:: bash

    $ sudo make uninstall && make && sudo make install

Note for maintainers
--------------------

Guake has drastically changed its build system with Guake 3. You may need to adapt all the
integration scripts accordingly.

Guake now uses `Pipfile` to store it Python dependencies (except the system dependencies such as
PyGTK3). It is maintained and used by `pipenv` CLI tool. It is a system more advanced than using
`requirements.txt`, but this file is still generated for backward compatibility (for example:
ReadTheDocs only support `requirements.txt` for the moment), by a tool I've developed, named
`pipenv_to_requirements` (makefile target `make requirements`).
It does generate `requirements.txt` (running dependencies), and `requirements-dev.txt` (build,
checks and test only). From then, Guake is now a classic, canon Python package (with setup.py,
building distrubution packages, ...).

It however requires system libraries, so cannot work isolated inside a virtualenv. If you look
closer to the virtualenv used with `make dev ; make run`, you will see it is configured to use
the system libraries using `pew toggleglobalsitepackages`.

If for any reason `pipenv` does not work on your platform, you can still install guake from these
requirements file, but the ultimate source of truth for dependency declaration is the `Pipfile`.

Do not hesitate to contact me at `gaetan [at] xeberon.net`.

Manual keybinding
-----------------

If you want to trigger guake manually, for instance on system where ``libkeybinder3`` does not work,
you can register the following snippet in your window manager

.. code-block:: bash

    dbus-send --type=method_call --dest=org.guake3.RemoteControl \
        /org/guake3/RemoteControl org.guake3.RemoteControl.show_hide

You can use the simpler

.. code-block:: bash

    guake -t

But it will be slower since ultimately it sends the very same D-Bus message.

Note on Wayland
---------------

There are some reports of Guake not opening when a Wayland app or empty desktop is focused.
The issue has been reported on Ubuntu 17.10 LTS, Fedora 26 and Fedora 27.
For more context, see issue #1041.

The workaround is setting a manual keybinding as described above. On Fedora 26, for example, this can be accomplished by
going to *Settings > Keyboard* and adding a new custom shortcut to execute :code:`guake -t`.

Contributing
============

First, be sure to use a verion of Python 3 where GTK and GObjects works in your system.
For instance, under Ubuntu 17.04, PyGtk and ``python3-gi`` does not work well if the default
python 3 interpreter is forced to Python 3.6.


| Operating System  | Recommended Python version |
| ----------------- | -------------------------- |
| Ubuntu 14.04 LTS  | Python 3.4 (UNTESTED)      |
| Ubuntu 16.04 LTS  | Python 3.5 (TESTED)        |
| Ubuntu 17.04      | Python 3.5 (TESTED)        |
| Ubuntu 17.10      | Python 3.6                 |

Install System dependencies
---------------------------

Ubuntu
~~~~~~

Execute the following command to bootstrap all needed system dependencies:

.. code-block:: bash

    $ ./bootstrap-dev-debian.sh

Setup development env
---------------------

Install the dependencies of your system and use the following commands:

.. code-block:: bash

    $ make dev
    $ sudo make install-schemas  # still required even for local execution

You can force the interpreter version using the PYTHON_INTERPRETER variable:

.. code-block:: bash

    $ make dev PYTHON_INTERPRETER=python3.6

Local execution of guake (without system-wide install):

.. code-block:: bash

    $ make run

Git hook
~~~~~~~~

Please install this git hook if you want to beautify your patch before submission:

.. code-block:: bash

    $ make setup-githook

Validate your code
~~~~~~~~~~~~~~~~~~

We are strict on code styling, with pep8 and pylint running automatically in travis in
order to reject badly shaped patches. Please use the following command to validate all
python files:

.. code-block:: bash

    $ make style  # fix the style of python files
    $ make check  # static code analysis
    $ make test   # unit test campaign
    $ make dists  # make distribution packages

Update translation
------------------

Update all translation files:

.. code-block:: bash

    $ make update-po

Install the translations files:

.. code-block:: bash

    $ sudo make install-locale

Then use your favorite po editor, such as ``poedit``.

Update NEWS
-----------

Update the `NEWS` file using the followng command:

.. code-block:: bash

    make release-note-news


The ``ChangeLog`` files is not maintained but instead automatically generated by PBR when
building the distribution packages.

Same goes for the `ChangeLog` file.

Versionning
-----------

Versioning is automatically done using git tags. When a semver tag is pushed, a new version
is automatically created by PBR.

Travis build
------------

Travis automatically check pull requests are compiling and check for code style.

Status of the master branch: https://travis-ci.org/Guake/guake.png?branch=master
