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
parser.add_option("--target",
                  action="store",
                  help=("Change the installation target. Available: 'virtualenv', 'system'. "
                        "Default: 'virtualenv'"),
                  choices=["virtualenv", "system"],
                  default="virtualenv")
parser.add_option("--tests",
                  action="store_true",
                  help="execute unit tests after installation")
parser.add_option("--checks",
                  action="store_true",
                  help="execute code integrity checks after installation")
parser.add_option("--update",
                  action="store_true",
                  help="update requirements.txt and requirements-dev.txt")
parser.add_option("--upgrade",
                  action="store_true",
                  help="See --update")
parser.add_option("--uninstall",
                  action="store",
                  help="Uninstall from the target. Available: 'virtualenv', 'system'",
                  choices=['virtualenv', 'system'])
parser.add_option("--clean",
                  action="store_true",
                  help=("Ensure environment is clean. Remove virtualenv if any. "
                        "It does NOT uninstall from the system"))

(options, args) = lib.parse(parser)

lib.printSeparator("=")
lib.printInfo("Guake Installation")
lib.printSeparator("=")
# lib.printDebug("Options: options: {!r}".format(options))
lib.printDebug("Args: args: {!r}".format(args))
lib.printDebug("Python version: %s", sys.version.partition("\n")[0])

dest_path = options.prefix
virtualenv_dest_path = os.path.abspath(os.path.join(g_src_dir, "venv"))
if lib.isWindows:
    activate_script = os.path.abspath(os.path.join(virtualenv_dest_path, "Scripts", "activate"))
else:
    activate_script = os.path.abspath(os.path.join(virtualenv_dest_path, "bin", "activate"))

if lib.isMacOsX or lib.isLinux:
    activate_link = os.path.abspath(os.path.join(g_src_dir, "activate"))
if options.clean:
    options.uninstall = "virtualenv"
    # TODO: if there are other thing to do, add here

if options.uninstall:
    if options.uninstall == "virtualenv":
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
    else:
        raise NotImplementedError("")

if os.environ.get("VIRTUAL_ENV"):
    lib.printInfo("Already in a virtual env, installing it inside this virtualenv")
    lib.printInfo("Installation in: {}".format(virtualenv_dest_path))
    lib.printInfo("VIRTUAL_ENV = %s", os.environ.get("VIRTUAL_ENV"))
    dest_path = virtualenv_dest_path
elif options.target == "virtualenv":
    dest_path = virtualenv_dest_path
    lib.checkVirtualEnv()

    if os.path.exists(activate_script):
        lib.printInfo("virtualenv already installed in %s", dest_path)
    else:
        lib.installVirtualEnv(dest_path, systemSitePackages=True)
    if lib.isMacOsX or lib.isLinux:
        if not os.path.exists(activate_link):
            lib.printInfo("Creating symbolic link %s", activate_link)
            lib.run(["ln", "-sf", activate_script, activate_link])

    lib.activateVirtualEnv(dest_path)
    if not os.environ.get("VIRTUAL_ENV"):
        lib.printError("Virtual environment not activated. Leaving")
        sys.exit(1)
    lib.printInfo("VIRTUAL_ENV = %s", os.environ.get("VIRTUAL_ENV"))
else:
    lib.printInfo("Installation in: {}".format(dest_path))
    raise NotImplementedError("system deployment not supported yet")

# Todo: check installed packages: python3-gi
dataFolder = "data"
pip_minversion = "pip==9.0.1"

lib.printInfo("Ensure pip is frozen")
lib.execute("pip install --upgrade {}".format(pip_minversion))
lib.printInfo("Installing direct dependencies")
lib.execute("pip install --upgrade -r requirements.txt")
if options.target == "virtualenv":
    lib.printInfo("Installing development dependencies")
    lib.execute("pip install --upgrade -r requirements-dev.txt")
    lib.execute("pip install --upgrade -e . --no-binary :all:")
    lib.execute("python setup.py sdist")

if options.checks:
    lib.execute("./validate.sh")

if options.tests:
    lib.execute("python setup.py test")

if options.upgrade:
    lib.printDebug("--upgrade parameter found. You mean --update")
    options.update = True

if options.update:
    lib.execute("pip-compile requirements-dev.in")
    lib.execute("pip-compile requirements.in")

if options.target == "virtualenv":
    lib.printInfo("Virtualenv can be enabled using 'source activate', and left with 'deactivate'")
