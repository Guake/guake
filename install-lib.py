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

import os
import shutil
import subprocess
import sys

from optparse import OptionParser

g_prefix = None
g_src_dir = os.path.abspath(os.path.dirname(__file__))

# Do *not* use optparse or argparse here, we are not sure on which version of python we are!

isWindows = False
if sys.platform.startswith('win32'):
    isWindows = True

#
# Utility functions
#


class bcolors(object):
    DEBUG = '\033[90m'
    HEADER = '\033[95m'
    OKBLUE = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BOOT = '\033[94m'
    ENDC = '\033[0m'

# Do *not* use color when:
#  - on windows
#  - not in a terminal except if we are in Travis CI
if (isWindows or (
        not os.environ.get("TRAVIS") and
        not sys.stdout.isatty() and
        not os.environ.get("TERM") in {
            "xterm",
            "xterm-256colors"
        })):
    bcolors.HEADER = ''
    bcolors.OKBLUE = ''
    bcolors.OKGREEN = ''
    bcolors.WARNING = ''
    bcolors.FAIL = ''
    bcolors.BOLD = ''
    bcolors.UNDERLINE = ''
    bcolors.BOOT = ''
    bcolors.ENDC = ''


def flush():
    sys.stdout.flush()
    sys.stderr.flush()


def printInfo(text):
    print(bcolors.OKBLUE + "[INFO ] " + bcolors.ENDC + text)
    flush()


def printDebug(text):
    print(bcolors.DEBUG + "[DEBUG] " + bcolors.ENDC + text, file=sys.stderr)
    flush()


def printError(text):
    print(bcolors.FAIL + "[ERROR] " + bcolors.ENDC + text, file=sys.stderr)
    flush()


def printSeparator(char="-", color=bcolors.OKGREEN):
    print(color + char * 79 + bcolors.ENDC)
    flush()


def printNote(text):
    print(bcolors.HEADER + "[NOTE ] " + bcolors.ENDC + text)
    flush()


def printBoot(text):
    print(bcolors.BOOT + "[BOOT ] " + bcolors.ENDC + text)
    flush()


def run(cmd, cwd=None, shell=False):
    print(bcolors.OKGREEN + "[CMD  ]" + bcolors.ENDC + " {}".format(" ".join(cmd)))
    flush()
    subprocess.check_call(cmd, shell=shell, cwd=cwd)


def call(cmd, cwd=None, shell=False):
    print(bcolors.OKGREEN + "[CMD  ]" + bcolors.ENDC + " {}".format(" ".join(cmd)))
    flush()
    return subprocess.call(cmd, shell=shell, cwd=cwd)


def run_background(cmd, cwd=None, shell=False):
    print(bcolors.OKGREEN + "[CMD (background)" + bcolors.ENDC + "] {}".format(" ".join(cmd)))
    flush()
    subprocess.Popen(cmd, cwd=cwd, shell=shell)


def execute(cmdLine):
    return run([cmdLine], shell=True)

#


def addArgumentParser(description=None):
    usage = "usage: %prog [options]\n\n{}".format(description)

    parser = OptionParser(usage=usage)
    parser.add_option("-p", "--prefix",
                      dest="prefix",
                      help="install architecture-independent files in PREFIX",
                      metavar="DIR",
                      default="/usr/local")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    return parser


def parse(parser):
    (options, args) = parser.parse_args()
    global g_prefix
    g_prefix = options.prefix
    return (options, args)


#

def makedirs(dirPath):
    try:
        os.makedirs(dirPath)
    except:
        pass


def copyFile(relativeSrcPath, relativeDestPath):
    printInfo("Copying {} to {}".format(relativeSrcPath, relativeDestPath))
    src_full_path = os.path.join(g_src_dir, relativeSrcPath)
    src_file_name = os.path.basename(relativeSrcPath)
    dst_full_path = os.path.join(g_prefix, relativeDestPath)
    printDebug("Src full path: {}".format(src_full_path))
    printDebug("Src file path: {}".format(src_file_name))
    printDebug("Dst full path: {}".format(dst_full_path))
    dst_dir = os.path.dirname(dst_full_path)
    makedirs(dst_dir)
    shutil.copy(src_full_path, dst_full_path)
    printDebug("{} -> {}".format(relativeSrcPath, dst_full_path))
