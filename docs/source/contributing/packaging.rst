============================
Help for Package maintainers
============================

This page is primarily targeted to package maintainers, willing to build and distribute Guake inside
a Linux Distribution, such as Debian, Arch, Fedora, and so on.

It gives some information about how Guake is built.

.. _Dependencies:

Dependencies
============

System dependencies
-------------------

Here are the system dependencies of Guake for its execution:

- GTK: >=3.18
- VTE: 2.91 (>=`0.42 <https://packages.ubuntu.com/xenial/gir1.2-vte-2.91>`_).
  See `doc here <https://lazka.github.io/pgi-docs/#Vte-2.91>`_
- ``gir1.2-keybinder-3.0``
- ``gir1.2-notify-0.7``
- ``gir1.2-vte-2.91``
- ``libkeybinder3``
- ``python3-cairo``
- ``python3-dbus``
- ``python3-gi``
- ``python3-pbr``

Optional dependencies:

- ``libutempter0``: compatibility with ``wall`` or ``screen`` commands
- Any GTK theme: ``numix-gtk-theme``, ...

Python dependencies
-------------------

The complete list of Python packages Guake requires for its execution is descripbed in the
``Pipfile``, section ``packages``.

Compatibility
=============

The Team is willing to see Guake available on every major Linux distribution. Do not hesitate to
contact us through GitHub Issue or directly by email (``gaetan [at] xeberon.net)`` if you see any
issue when packageing Guake.

The major compatibility issues we experience if with the different version of VTE. We try to
integrate new cool VTE features when they are ready, and protect them with test on the version
installed on the user's environment, but there may still be mistakes made, breaking the software
for a given environment. Do not hesitate to warn us for that!
