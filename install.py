#!/usr/bin/env python3

# Beware:
#  - this script is executed using the system's python, so with not easy control on which
#    packages are available. Same, we cannot directly install new ones using pip.
#  - the role of the first stage of this installer is just to install a fresh new virtualenv
#    with a *controled* version of python, pip and virtualenv, and launch the second part of
#    the installer, 'install-stage2.py', which will run in the virtualenv.

# Note:
#  - This script should execute transparently in an Python > 2.7 or Python > 3.4 without any
#    additional packages

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import imp
import os
import shutil
import sys

g_prefix = None
g_src_dir = os.path.abspath(os.path.dirname(__file__))

# Injecting available targets from installer stage 2
lib = imp.load_source('install_lib.py',
                      os.path.join(os.path.dirname(__file__), "install_lib.py"))


def copyFile(relativeSrcPath, relativeDestPath):
    lib.printInfo("Copying {} to {}".format(relativeSrcPath, relativeDestPath))
    src_full_path = os.path.join(g_src_dir, relativeSrcPath)
    src_file_name = os.path.basename(relativeSrcPath)
    dst_full_path = os.path.join(g_prefix, relativeDestPath)
    lib.printDebug("Src full path: {}".format(src_full_path))
    lib.printDebug("Src file path: {}".format(src_file_name))
    lib.printDebug("Dst full path: {}".format(dst_full_path))
    dst_dir = os.path.dirname(dst_full_path)
    lib.makedirs(dst_dir)
    shutil.copy(src_full_path, dst_full_path)
    lib.printDebug("{} -> {}".format(relativeSrcPath, dst_full_path))


parser = lib.addArgumentParser(description="Install Guake on your system")
parser.add_option("--dev",
                  action="store_true",
                  help="install guake in a virtualenv (for developers)")
parser.add_option("--tests",
                  action="store_true",
                  help="execute unit tests")
parser.add_option("--checks",
                  action="store_true",
                  help="execute code integrity checks")
parser.add_option("--update",
                  action="store_true",
                  help="update requirements.txt and requirements-dev.txt")
parser.add_option("--uninstall-system",
                  action="store_true",
                  help="uninstall from the system")
parser.add_option("--uninstall-dev",
                  action="store_true",
                  help="uninstall local virtual env")
(options, args) = lib.parse(parser)

lib.printSeparator("=")
lib.printInfo("Guake Installation")
lib.printSeparator("=")
lib.printDebug("Options: options: {!r}".format(options))
lib.printDebug("Args: args: {!r}".format(args))
lib.printDebug("Python version: %s", sys.version.partition("\n")[0])

dest_path = options.prefix
virtualenv_dest_path = os.path.abspath(os.path.join(g_src_dir, "workdir"))
if lib.isWindows:
    activate_script = os.path.abspath(os.path.join(virtualenv_dest_path, "bin", "activate"))
else:
    activate_script = os.path.abspath(os.path.join(virtualenv_dest_path, "Scripts", "activate"))

if lib.isMacOsX or lib.isLinux:
    activate_link = os.path.abspath(os.path.join(g_src_dir, "activate"))
if options.uninstall_dev:
    lib.printSeparator()
    lib.printDebug("Uninstalling virtualenv")
    lib.printSeparator()
    lib.rmrv(virtualenv_dest_path)
    lib.rmrv(activate_link)
    lib.rmrv(os.path.join(g_src_dir, "__pycache__"))
    lib.rmrv(os.path.join(g_src_dir, "Guake.egg-info"))
    lib.rmrv(os.path.join(g_src_dir, "pbr-1.8.1-py2.7.egg"))
    lib.printInfo("Guake3 virtualenv uninstalled")
    sys.exit(0)

if os.environ.get("VIRTUAL_ENV"):
    lib.printInfo("Already in a virtual env, installing it inside this virtualenv")
    lib.printInfo("Installation in: {}".format(virtualenv_dest_path))
    lib.printInfo("VIRTUAL_ENV = %s", os.environ.get("VIRTUAL_ENV"))
    dest_path = virtualenv_dest_path
elif options.dev:
    dest_path = virtualenv_dest_path
    lib.checkVirtualEnv()

    if os.path.exists(activate_script):
        lib.printInfo("virtualenv already installed in %s", dest_path)
    else:
        lib.installVirtualEnv(dest_path)
    if lib.isMacOsX or lib.isLinux:
        if not os.path.exists(activate_link):
            lib.printInfo("Creating symbolic link %s", activate_link)
            lib.run(["ln", "-s", activate_script, activate_link])

    lib.activateThis(dest_path)
    lib.printInfo("VIRTUAL_ENV = %s", os.environ.get("VIRTUAL_ENV"))
else:
    lib.printInfo("Installation in: {}".format(dest_path))

dataFolder = "data"

lib.execute("pip install --upgrade pip")
lib.execute("pip install --upgrade -r requirements.txt")
if options.dev:
    lib.execute("pip install --upgrade -r requirements-dev.txt")
    lib.execute("pip install --upgrade -e . --no-use-wheel")

if options.checks:
    lib.execute("./validate.sh")

if options.tests:
    lib.execute("py.test guake/tests")

if options.update:
    lib.execute("pip-compile requirements-dev.in")
    lib.execute("pip-compile requirements.in")

if options.dev:
    lib.printInfo("Virtualenv can be enabled using 'source activate', and left with 'deactivate'")
