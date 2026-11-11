Frequently Asked Questions
==========================

Manual keybinding
-----------------

If you want to trigger guake manually, for instance on system where ``libkeybinder3`` does not work,
you can register the following snippet in your window manager

.. code-block:: bash

    dbus-send --type=method_call --dest=org.guake3.RemoteControl \
        /org/guake3/RemoteControl org.guake3.RemoteControl.show_hide

You can use the simpler:

.. code-block:: bash

    guake-toggle

Please note the command `guake -t` will also toggle Guake but since it initialize a bit more than just
necessary, it can be slower that the two previous commands.

Note on Wayland
---------------

There are some reports of Guake not opening when a Wayland app or empty desktop is focused.
The issue has been reported on Ubuntu 17.10 LTS, Fedora 26 and Fedora 27.
For more context, see issue #1041.

The workaround is setting a manual keybinding as described above.
On Fedora 26, for example, this can be accomplished by going to *Settings > Keyboard* and
adding a new custom shortcut to execute :code:`guake-toggle`.

Running Guake as a native Wayland client
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Guake sets the X11 GDK backend at startup (see ``guake/main.py``), because that is still the backend
where most things work, global shortcuts in particular. If you would rather have Guake talk to
Wayland directly, set the ``GUAKE_ENABLE_WAYLAND`` environment variable:

.. code-block:: bash

    $ GUAKE_ENABLE_WAYLAND=1 guake

Only the presence of the variable is checked, its value does not matter, so
``GUAKE_ENABLE_WAYLAND=0`` turns Wayland on as well. Unset it to get the X11 backend back.

The variable is read when Guake starts, so it has to be in Guake's own environment. Putting it in
your shell rc file only covers instances you launch from that shell, not the one GNOME starts at
login. For that case a systemd user environment file is read early enough:

.. code-block:: bash

    $ mkdir -p ~/.config/environment.d
    $ echo "GUAKE_ENABLE_WAYLAND=1" > ~/.config/environment.d/guake-wayland.conf

and takes effect at the next login. Editing the ``Exec=`` line of the desktop entry you launch
Guake from works too, but note that with *Start Guake at login* enabled Guake rewrites
``~/.config/autostart/guake.desktop`` from the packaged template on every start, so changes made
there are lost.

Wayland does not let an application grab global shortcuts, so Guake cannot register the show/hide
key itself and has to leave it to the desktop, as described above. If you get a *problem happened
when binding* notification on every launch, switch the builtin binding off with:

.. code-block:: bash

    $ gsettings set guake.keybindings.global show-hide "disabled"

Note for Archlinux users
------------------------

This applies to users of Archlinux based distributions too and may be of help to non
Debian/Ubuntu users as well. Currently ``make install`` is optimized for Ubuntu, which
does not mean that it cannot be used on other systems, but depending on your system
you may have to tell ``make install`` where to install guake
(the default for Ubuntu is ``/usr/local/lib/python3.x/dist-packages/guake``).

So on Ubuntu the following commands are equivalent:

.. code-block:: bash

    $ sudo make install
    $ sudo make install PREFIX=/usr/local

On Archlinux this can be done by passing ``/usr`` as ``PREFIX``:

.. code-block:: bash

    $ sudo make install PREFIX=/usr

which changes the installation destination to ``/usr/lib/python3.x/site-packages/guake``.

Note that the install script automatically determines whether to use
``dist-packages`` or ``site-packages``.

For more details checkout the official PKGBUILD at
`archlinux.org <https://www.archlinux.org/packages/community/any/guake/>`_, the PKGBUILD on
the `aur <http://aur.archlinux.org/packages/guake-git>`_ or this
`gist <https://gist.github.com/aichingm/ed35ba3b136be4424b1ac947207dbca3>`_.

Why Guake crashes with Tmux and Byubu?
--------------------------------------

Tmux and Byobu can be used as shell instead of bash or zsh, but you should be sure to disable the
"use login shell" option. If set, Guake will not be able to start. Use ``dconf-editor`` to reset
this option if Guake cannot start again.
