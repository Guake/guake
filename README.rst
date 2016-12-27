Guake 3 README
==============

Setting up a developer's environment
------------------------------------

First, you need to install some system libraries, mainly GTK and related.

- On Ubuntu and Debian, use:

      ./bootstrap-debian.sh

Now, install Guake inside a new virtualenv with:

    ./install.py

Setting up to your system
-------------------------

    ./install.py --target=system

Note: not supported yet. Installing on your system directly is a **wrong** idea. It should always be
installed in a proper virtualenv, to avoid messing with your system modules. Of course, Guake relies
on VTE and GTK modules that shall come from your system, but there is no reason to let Guake
override any python package of your system.

When Guake is packaged in a distribution (Ubuntu, Debian, Fedora,...), in this case only it makes
sense to install it outside of a virtualenv.
However, please see:
    https://hynek.me/articles/python-deployment-anti-patterns/
