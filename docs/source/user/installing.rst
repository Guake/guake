================
Installing Guake
================

System-wide installation
========================

Always prefere using your package manager to install guake.

Debian / Ubuntu
---------------

Ubuntu and Debian users will use ``sudo apt install guake``.

Fedora
------

TBD: Want to help fill this section? Please submit your suggestion on
`GitHub <https://github.com/Guake/guake>`_.

Arch Linux
----------

TBD: Want to help fill this section? Please submit your suggestion on
`GitHub <https://github.com/Guake/guake>`_.

Install from Pypi
=================

Guake is now automatically published on Pypi.
Please use the following command to install on your environment:

.. code-block:: bash

    $ pip install --user guake


Avoid using ``pip install guake`` without the ``--user``, you may break
your system.

Install from source
===================

If you want to install Guake from its sources make sure that you have the 
needed dependencies installed. If you are unsure about the dependencies you 
can run to install them:

.. code-block:: bash
    $bash scripts/bootstrap-dev-[debian, arch, fedora].sh run make

Note: Insert your distribution in the square brackets.

To install Guake itself, use:

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
    $ # Or use this shortcut:
    $ make reinstall  # (do not sudo it!)
