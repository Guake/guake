# Copyright (C) 2007 Gabriel Falcão <gabrielteratos@gmail.com>
# Copyright (C) 2007 Lincoln de Sousa <lincoln@archlinux-br.org>
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

AC_INIT([guake], [0.1], [lincoln@archlinux-br.org])

AC_CONFIG_HEADERS([config.h])

AC_CONFIG_MACRO_DIR([m4])

AM_INIT_AUTOMAKE([-Wall -Werror])

AC_PROG_LIBTOOL

AC_PROG_CC

AC_PROG_INTLTOOL

dnl python checks
AM_PATH_PYTHON(2.4.0)

PY_PREFIX=`$PYTHON -c 'import sys ; print sys.prefix'`
PYTHON_LIBS="-lpython$PYTHON_VERSION"
PYTHON_CFLAGS="-I$PY_PREFIX/include/python$PYTHON_VERSION"

AC_SUBST([PYTHON_LIBS])
AC_SUBST([PYTHON_CFLAGS])

dnl gtk dependencie
GTK_REQUIRED=2.10.0
PKG_CHECK_MODULES([DEPENDENCIES], [
    gtk+-2.0 >= $GTK_REQUIRED
])
AC_SUBST([DEPENDENCIES_CFLAGS])
AC_SUBST([DEPENDENCIES_LIBS])

dnl expanding useful variables
AS_AC_EXPAND(LIBDIR, ${libdir})
AS_AC_EXPAND(BINDIR, ${bindir})
AS_AC_EXPAND(DATADIR, ${datarootdir})

dnl gconf
AC_PATH_PROG(GCONFTOOL, gconftool-2, no)
if test x"$GCONFTOOL" = xno; then
    AC_MSG_ERROR([gconftool-2 executable not found in your path - should be installed with GConf])
fi
AM_GCONF_SOURCE_2

dnl Internationalization
GETTEXT_PACKAGE=guake
ALL_LINGUAS="pt_BR"

AC_SUBST([GETTEXT_PACKAGE])
AC_SUBST([ALL_LINGUAS])

AM_GLIB_GNU_GETTEXT

dnl output files
AC_CONFIG_FILES([
    Makefile
    data/Makefile
    data/guake.desktop
    data/org.gnome.Guake.service
    data/pixmaps/Makefile
    po/Makefile.in
    src/Makefile
    src/globalhotkeys/Makefile
    src/guake_globals.py
    src/guake
])

AC_OUTPUT
