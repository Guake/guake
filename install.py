#!/usr/bin/env python

# Beware:
#  - this script is executed using the system's python, so with not easy control on which
#    packages are available. Same, we cannot directly install new ones using pip.
#  - the role of the first stage of this installer is just to install a fresh new virtualenv
#    with a *controled* version of python, pip and virtualenv, and launch the second part of
#    the installer, 'install-stage2.py', which will run in the virtualenv.

# Note:
#  - I try to keep this installer python-2.6 friendly, but I really encourage you to install
#    Python 2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import imp
import os

# Injecting available targets from installer stage 2
lib = imp.load_source('install-lib.py',
                      os.path.join(os.path.dirname(__file__), "install-lib.py"))

parser = lib.addArgumentParser(description="Install Guake on your system")
(options, args) = lib.parse(parser)

lib.printSeparator("=")
lib.printInfo("Guake Installation")
lib.printSeparator("=")
lib.printDebug("Options: options: {!r}".format(options))
lib.printDebug("Args: args: {!r}".format(args))

lib.printInfo("Installation in: {}".format(options.prefix))

dataFolder = "data-gtk3"


def copyDataFile(filename, dstPath):
    lib.copyFile(os.path.join(dataFolder, filename), dstPath)

copyDataFile("guake.schema", "share/glib-2.0/schemas/org.gnome.gschema.xml")
lib.execute("sudo glib-compile-schemas {prefix}/share/glib-2.0/schemas/"
            .format(prefix=options.prefix))
