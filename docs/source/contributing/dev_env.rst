======================================
Setting up the development environment
======================================

Before building the code, please ensure the dependencies are installed:

- GTK: >=3.18
- VTE: 2.91
- ``libkeybinder3``

See full list of dependencies on the :ref:`Dependencies` page.

The following section describes how to install these dependencies on some systems, please be
aware it might not be applicable to yours directly.

Install System dependencies
===========================

Ubuntu
------

Execute the following command to bootstrap all needed system dependencies:

.. code-block:: bash

    $ ./scripts/bootstrap-dev-debian.sh

Fedora
------

Execute:

.. code-block:: bash

    $ ./scripts/bootstrap-dev-fedora.sh

Arch Linux
----------

Execute:

.. code-block:: bash

    $ ./scripts/bootstrap-dev-arch.sh

Setup development environment
=============================

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

Install on system
=================

Use the following command to build and install on your system (in ``/usr/local/``):

.. code-block:: bash

    $ make dev && make && sudo make install


You can reinstall easily in your environment (only validated for Debian/Ubuntu) with:

.. code-block:: bash

    $ make reinstall  # will execute `sudo`

Git hook
========

This project uses `pre-commit <https://pre-commit.com/>` to automatically execute some codestyle tools. It should be automatically installed by the ``make dev`` command, you can use ``make style`` if you want to run it manually. If you want to pass more options, you can use:

.. code-block:: bash

    $ pipenv run pre-commit run --all-files
