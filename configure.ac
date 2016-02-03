# Copyright (C) 2007-2014 Guake authors
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

AC_INIT([guake], [0.8.5], [http://guake-project.org/])

AC_CONFIG_HEADERS([config.h])

AC_CONFIG_MACRO_DIR([m4])

AM_INIT_AUTOMAKE([-Wall -Werror -Wno-extra-portability foreign])

AC_PROG_LIBTOOL

AC_PROG_CC

AC_PROG_INTLTOOL([0.35.0])
AM_GLIB_GNU_GETTEXT

dnl python checks
AM_PATH_PYTHON(2.7)

PY_PREFIX=`$PYTHON -c 'import sys ; print sys.prefix'`
PYTHON_LIBS="-lpython$PYTHON_VERSION"
PYTHON_CFLAGS="-I$PY_PREFIX/include/python$PYTHON_VERSION"

AC_SUBST([PYTHON_LIBS])
AC_SUBST([PYTHON_CFLAGS])

dnl gtk dependency
GTK_REQUIRED=2.10.0
PKG_CHECK_MODULES([DEPENDENCIES], [
    gtk+-2.0 >= $GTK_REQUIRED
    pygtk-2.0
    x11
])
AC_SUBST([DEPENDENCIES_CFLAGS])
AC_SUBST([DEPENDENCIES_LIBS])

dnl expanding useful variables
AS_AC_EXPAND(LIBDIR, ${libdir})
AS_AC_EXPAND(BINDIR, ${bindir})
AS_AC_EXPAND(DATADIR, ${datarootdir})

dnl Checking python-vte
AC_MSG_CHECKING([for the python-vte package])
ac_pvte_result=`$PYTHON -c 'try:
    import vte
except Exception, e:
    print str(e)' 2> /dev/null`

if test -z "$ac_pvte_result"; then
    AC_MSG_RESULT([yes])
else
    AC_MSG_RESULT([no])
    AC_MSG_ERROR([cannot import Python module "vte".
    Please check if you have python-vte installed. The error was:
    $ac_pvte_result])
fi

dnl gconf
AC_PATH_PROG(GCONFTOOL, gconftool-2, no)
if test x"$GCONFTOOL" = xno; then
    AC_MSG_ERROR([gconftool-2 executable not found in your path - should be installed with GConf])
fi
AM_GCONF_SOURCE_2

dnl Internationalization
GETTEXT_PACKAGE=guake
ALL_LINGUAS="ca cs de el es fa fr gl hr hu id it ja ko nb nl pa pl pt_BR ru sv tr uk zh_CN"

AC_SUBST([GETTEXT_PACKAGE])
AC_SUBST([ALL_LINGUAS])

dnl output files
AC_CONFIG_FILES([
    Makefile
    data/Makefile
    data/guake.desktop
    data/guake-prefs.desktop
    data/org.guake.Guake.service
    data/pixmaps/Makefile
    data/icons/Makefile
    po/Makefile.in
    src/guake/Makefile
    src/guake/globals.py
    doc/src/conf.py
])

AC_OUTPUT
