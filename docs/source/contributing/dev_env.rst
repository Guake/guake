======================================
Setting up the development environment
======================================

Install System dependencies
---------------------------

Ubuntu
~~~~~~

Execute the following command to bootstrap all needed system dependencies:

.. code-block:: bash

    $ ./scripts/bootstrap-dev-debian.sh

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

You can reinstall easily in your environment (only validated for Debian/Ubuntu) with:

.. code-block:: bash

    $ make reinstall  # will execute `sudo`

Git hook
~~~~~~~~

Please install this git hook if you want to beautify your patch before submission:

.. code-block:: bash

    $ make setup-githook
