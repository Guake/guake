'''
Install Utility

This module allows to bootstrap your developer environment with an easy to write "install" script
that will replace the need to use external tools such as configure, automake, etc. Everything
happens in Python!

Ex:

    from __future__ import absolute_import
    from __future__ import division
    from __future__ import print_function
    from __future__ import unicode_literals

    import imp

    # Injecting available targets from installer stage 2
    lib = imp.load_source('install-lib.py',
                          os.path.join(os.path.dirname(__file__), "install-lib.py"))


This "install" script you will write will have the following properties:

- it can be run **outside** of a virtual env, so it will not benefit from all the fancy packages you
  will use in your Python program.
- it handles the installation on the destination system (equivalent to ``sudo make install``)
- for development, it will automatically create the virtualenv.

Your environment can be automatically compatible with integrated tools such Travis or Pipy that only
needs the requirements.txt and setup.py to be setup, while you, as a developer, can install or set
up you environment in a single shot.


'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import errno
import os
import platform
import shutil
import subprocess
import sys

isWindows = sys.platform.startswith('win32')
isLinux = sys.platform.startswith("linux")
isMacOsX = sys.platform.startswith("darwin")
isUbuntu = False
# pylint: disable=deprecated-method
_distrib = platform.linux_distribution()
# pylint: enable=deprecated-method

if len(_distrib) == 3 and _distrib[0].lower() == "ubuntu":
    isUbuntu = True
    ubuntuVersion = _distrib[1]
    ubuntuVersionMajor = int(ubuntuVersion.partition('.')[0])
    ubuntuVersionInt = ubuntuVersionMajor * 100 + int(ubuntuVersion.partition('.')[2])

####################################################################################################
# Utility functions
####################################################################################################


class AsciiColor(object):
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
if isWindows or (not os.environ.get("TRAVIS") and not sys.stdout.isatty()):
    AsciiColor.HEADER = ''
    AsciiColor.OKBLUE = ''
    AsciiColor.OKGREEN = ''
    AsciiColor.WARNING = ''
    AsciiColor.FAIL = ''
    AsciiColor.BOLD = ''
    AsciiColor.UNDERLINE = ''
    AsciiColor.BOOT = ''
    AsciiColor.ENDC = ''


def flush():
    sys.stdout.flush()
    sys.stderr.flush()


def printInfo(text, *args):
    text = str(text)
    if args:
        text = text % args
    for line in text.split("\n"):
        print(AsciiColor.OKBLUE + "[INFO ] " + AsciiColor.ENDC + line)
    flush()


def printError(text, *args):
    text = str(text)
    if args:
        text = text % args
    for line in text.split("\n"):
        print(AsciiColor.FAIL + "[ERROR] " + AsciiColor.ENDC + line, file=sys.stderr)
    flush()


def printSeparator(char="-", color=AsciiColor.OKGREEN):
    print(color + char * 79 + AsciiColor.ENDC)
    flush()


def printNote(text, *args):
    text = str(text)
    if args:
        text = text % args
    for line in text.split("\n"):
        print(AsciiColor.HEADER + "[NOTE ] " + AsciiColor.ENDC + line)
    flush()


def printBoot(text, *args):
    text = str(text)
    if args:
        text = text % args
    for line in text.split("\n"):
        print(AsciiColor.BOOT + "[BOOT ] " + AsciiColor.ENDC + line)
    flush()


def printDebug(text, *args):
    text = str(text)
    if args:
        text = text % args
    for line in text.split("\n"):
        print(AsciiColor.BOOT + "[DEBUG] " + AsciiColor.ENDC + line)
    flush()


def printCmd(text):
    text = str(text)
    for line in text.split("\n"):
        print(AsciiColor.OKGREEN + "[CMD  ] " + AsciiColor.ENDC + line)
    flush()


def printQuestion(text, *args):
    text = str(text)
    if args:
        text = text % args
    for line in text.split("\n"):
        print(AsciiColor.OKGREEN + "[???? ] " + AsciiColor.ENDC + line)
    flush()
    line = sys.stdin.readline()
    return line.strip()


def run(cmd, cwd=None, shell=False, extraPath=None):
    print(AsciiColor.OKGREEN + "[CMD  ]" + AsciiColor.ENDC + " {}".format(" ".join(cmd)))
    flush()
    path_bkp = None
    if extraPath and not isWindows:
        # Force use shell to allow PATH environment variable propagation
        shell = True
        path_bkp = os.environ['PATH']
        os.environ['PATH'] = extraPath + ":" + os.environ['PATH']
        cmd = " ".join(cmd)
        print(AsciiColor.OKGREEN + "[CMD  ]" + AsciiColor.ENDC +
              " PATH set to: {}".format(os.environ['PATH']))
    subprocess.check_call(cmd, shell=shell, cwd=cwd)
    if extraPath and path_bkp:
        os.environ['PATH'] = path_bkp


def runOutput(cmd, cwd=None, shell=False):
    print(AsciiColor.OKGREEN + "[CMD  ]" + AsciiColor.ENDC + " {}".format(" ".join(cmd)))
    flush()
    s = subprocess.check_output(cmd, shell=shell, cwd=cwd)
    return str(s)


def runNocheck(cmd, cwd=None, shell=False):
    try:
        print(AsciiColor.OKGREEN + "[CMD  ]" + AsciiColor.ENDC + " {}".format(" ".join(cmd)))
        flush()
        subprocess.check_call(cmd, shell=shell, cwd=cwd)
    except Exception as e:
        printError("Exception : {}".format(e))


def call(cmd, cwd=None, shell=False):
    print(AsciiColor.OKGREEN + "[CMD  ]" + AsciiColor.ENDC + " {}".format(" ".join(cmd)))
    flush()
    return subprocess.call(cmd, shell=shell, cwd=cwd)


def runBackground(cmd, cwd=None, shell=False):
    print(AsciiColor.OKGREEN + "[CMD (background)" + AsciiColor.ENDC + "] {}".format(" ".join(cmd)))
    flush()
    subprocess.Popen(cmd, cwd=cwd, shell=shell)


def mkdirs(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def execute(cmdLine):
    return run([cmdLine], shell=True)


def testExec(executable):
    try:
        run(['bash', '-c', "which " + executable])
        return True
    except Exception:
        return False


if isUbuntu and ubuntuVersionInt <= 1404:
    virtualenv_exec = "virtualenv"
    virtualenv_cmd = ["virtualenv", "-p", "python3"]
else:
    virtualenv_exec = "pyvenv"
    virtualenv_cmd = "pyvenv"


def checkVirtualEnv():
    printInfo("Checking if 'virtualenv' is installed...")
    if not testExec(virtualenv_exec):
        printError("'%s' does not seems installed on your system!", virtualenv_exec)
        if isUbuntu:
            if ubuntuVersionInt <= 1404:
                printError("Please install with 'sudo apt-get install python3-pip ; "
                           "sudo pip3 install virtualenv'")
            else:
                printError("Please install with 'sudo apt-get install python3-venv'")
        else:
            printError("Please install it")
        sys.exit(1)


def installVirtualEnv(destPath):
    run(virtualenv_cmd + [destPath])


def addArgumentParser(description=None):
    usage = "usage: %prog [options]\n\n{}".format(description)

    from optparse import OptionParser
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
    return (options, args)


def makedirs(dirPath):
    try:
        os.makedirs(dirPath)
    except Exception:
        pass


def execfile(filepath, globalVars, localVars=None):
    with open(filepath) as f:
        code = compile(f.read(), "somefile.py", 'exec')
        exec(code, globalVars, localVars)


def rmdir(path):
    '''
    Remove a given directory. Do not fail if it does not exist
    '''
    if os.path.exists(path):
        shutil.rmtree(path)


def rmrv(f):
    '''
    Dangerous equivalent to 'rm -rf'.
    '''
    if os.path.islink(f):
        os.unlink(f)
    elif not os.path.exists(f):
        return
    elif os.path.isdir(f):
        rmdir(f)
    else:
        os.unlink(f)


def activateThis(sandbox):
    '''
    Activate sandbox
    '''
    if isWindows:
        sandbox_bin = os.path.abspath(os.path.join(sandbox, "Scripts"))
    else:
        sandbox_bin = os.path.abspath(os.path.join(sandbox, "bin"))
    sandbox = os.path.abspath(sandbox)
    printSeparator()
    printInfo("Activating sandbox %s", sandbox_bin)
    printSeparator()
    old_os_path = os.environ.get('PATH', '')
    os.environ['PATH'] = os.path.abspath(sandbox_bin) + os.pathsep + old_os_path
    if sys.platform == 'win32':
        site_packages = os.path.join(sandbox, 'Lib', 'site-packages')
    else:
        site_packages = os.path.join(sandbox, 'lib', 'python%s' % sys.version[:3], 'site-packages')
    printDebug("site_packages = %r", site_packages)
    prev_sys_path = list(sys.path)
    import site
    site.addsitedir(site_packages)
    sys.real_prefix = sys.prefix
    sys.prefix = sandbox
    # Move the added items to the front of the path:
    new_sys_path = []
    for item in list(sys.path):
        if item not in prev_sys_path:
            new_sys_path.append(item)
            sys.path.remove(item)
    sys.path[:0] = new_sys_path
