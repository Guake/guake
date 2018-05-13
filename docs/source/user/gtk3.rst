
Gtk 3 Port
==========

Early 2018, Guake has been ported Gtk3, thanks to the huge work of @aichingm.
Old releases and code depending on GTK2 have been put on the
`0.8.x <https://github.com/Guake/guake/tree/0.8.x>`_ branch
of the GitHub project and will no more be actively maintained.

Please note that we target to support mainly the GTK and VTE versions found
by default on most popular distribution such as Ubuntu or Arch Linux
(currently: Ubuntu 16.04 LTS and 17.10).

Guake is now only compatible with Python 3.5+.

Port to Gtk 3 and Python 3 lead naturally to skip all 1.x and 2.x version in the
version of Guake: Guake 3.

Dropped Features from Guake 0.8.x
---------------------------------

- ``--bgimg`` (this option has been removed from vte)

Broken translations
-------------------

Some changes in translation system made during the Guake 3 port may have broken the welcome message
in some languages (#1209).

Help is welcomed for updating translations in your language ! See the "Update translation" section
bellow.

Note for maintainers
--------------------

Guake has drastically changed its build system with Guake 3. You may need to adapt all the
integration scripts accordingly.

Guake now uses ``Pipfile`` to store it Python dependencies (except the system dependencies such as
PyGTK3). It is maintained and used by `pipenv` CLI tool. It is a system more advanced than using
``requirements.txt``, but this file is still generated for backward compatibility (for example:
ReadTheDocs only support ``requirements.txt`` for the moment), by a tool I've developed, named
``pipenv_to_requirements`` (makefile target ``make requirements``).
It does generate ``requirements.txt`` (running dependencies), and ``requirements-dev.txt`` (build,
checks and test only). From then, Guake is now a classic, canon Python package (with setup.py,
building distrubution packages, ...).

It however requires system libraries, so cannot work isolated inside a virtualenv. If you look
closer to the virtualenv used with ``make dev ; make run``, you will see it is configured to use
the system libraries using ``pew toggleglobalsitepackages``.

If for any reason ``pipenv`` does not work on your platform, you can still install guake from these
requirements file, but the ultimate source of truth for dependency declaration is the ``Pipfile``.

Do not hesitate to contact me at ``gaetan [at] xeberon.net``.
