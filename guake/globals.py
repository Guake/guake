# -*- coding: utf-8; -*-
"""
Copyright (C) 2007-2013 Guake authors

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor,
Boston, MA 02110-1301 USA
"""

import inspect
import logging
import os

__all__ = [
    "ALIGN_BOTTOM",
    "ALIGN_CENTER",
    "ALIGN_LEFT",
    "ALIGN_RIGHT",
    "ALIGN_TOP",
    "ALWAYS_ON_PRIMARY",
    "NAME",
]

log = logging.getLogger(__name__)


def bindtextdomain(app_name, locale_dir=None):
    """
    Bind the domain represented by app_name to the locale directory locale_dir.
    It has the effect of loading translations, enabling applications for different
    languages.

    app_name:
        a domain to look for translations, typically the name of an application.

    locale_dir:
        a directory with locales like locale_dir/lang_isocode/LC_MESSAGES/app_name.mo
        If omitted or None, then the current binding for app_name is used.
    """

    # pylint: disable=import-outside-toplevel
    import locale

    # pylint: enable=import-outside-toplevel

    log.info("Local binding for app '%s', local dir: %s", app_name, locale_dir)

    locale.bindtextdomain(app_name, locale_dir)
    locale.textdomain(app_name)


def is_run_from_git_workdir():
    self_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
    return os.path.exists(f"{self_path}.in")


NAME = "guake"

ALIGN_CENTER, ALIGN_LEFT, ALIGN_RIGHT = range(3)
ALIGN_TOP, ALIGN_BOTTOM = range(2)
ALWAYS_ON_PRIMARY = -1

# TODO this is not as fancy as as it could be
# pylint: disable=anomalous-backslash-in-string
TERMINAL_MATCH_TAGS = ("schema", "http", "https", "email", "ftp")
# Beware this is a PRCE (Perl) regular expression, not a Python one!
# Edit: use regex101.com with PCRE syntax
TERMINAL_MATCH_EXPRS = [
    r"(news:|telnet:|nntp:|file:\/|https?:|ftps?:|webcal:)\/\/([-[:alnum:]]+"
    r"(:[-[:alnum:],?;.:\/!%$^\*&~\"#']+)?\@)?[-[:alnum:]]+(\.[-[:alnum:]]+)*"
    r"(:[0-9]{1,5})?(\/[-[:alnum:]_$.+!*(),;:@&=?\/~#%]*[^]'.>) \t\r\n,\\\"])?",
    r"(www|ftp)[-[:alnum:]]*\.[-[:alnum:]]+(\.[-[:alnum:]]+)*(:[0-9]{1,5})?"
    r"(\/[-[:alnum:]_$.+!*(),;:@&=?\/~#%]*[^]'.>) \t\r\n,\\\"])?",
    r"(mailto:)?[-[:alnum:]][-[:alnum:].]*@[-[:alnum:]]+\.[-[:alnum:]]+(\\.[-[:alnum:]]+)*",
]
# tuple (title/quick matcher/filename and line number extractor)
QUICK_OPEN_MATCHERS = [
    (
        "Python traceback",
        r"^\s*File\s\".*\",\sline\s[0-9]+",
        r"^\s*File\s\"(.*)\",\sline\s([0-9]+)",
    ),
    (
        "Python traceback 2",
        r"^\s*.*\:\sline\s[0-9]+",
        r"^\s*(.*)\:\sline\s([0-9]+)",
    ),
    (
        "Php traceback",
        r"^\s*.*\:\son\sline\s[0-9]+",
        r"^\s*(.*)\:\son\sline\s([0-9]+)",
    ),
    (
        "Php traceback 2",
        r"^\s*.*\:\s*.*\sin\s*.*\:\son\sline\s[0-9]+",
        r"^\s*.*\:\s*.*\sin\s(.*)\:\son\sline\s([0-9]+)",
    ),
    (
        "Python traceback Spanish",
        r"^\s*Archivo\s\".*\",\slinea\s[0-9]+",
        r"^\s*Archivo\s\"(.*)\",\slinea\s([0-9]+)",
    ),
    (
        "vite line starts by 'html:/home/_components/Base.svelte:5:25: error: Expected'",
        r"^html\:.*\:[0-9]+",
        r"^html\:(.*)\:([0-9]+)",
    ),
    (
        "vite line starts by ' > html:/home/_components/Slider.svelte:12:16: error: Expected'",
        r"^\s\>\shtml\:.*\:[0-9]+",
        r"^\s\>\shtml\:(.*)\:([0-9]+)",
    ),
    (
        "vite line starts by '  File: /home/_components/_icons.svelte '",
        r"^\sFile\:\s.*\s",
        r"^\sFile\:\s(.*)\s",
    ),
    (
        "vite line starts by '  at error (/home/.svelte@3.35.0/co.js:16752:20)'",
        r"^\sat\serror\s\(.*\:[0-9]+\)",
        r"^\sat\serror\s\((.*)\:([0-9]+)\)",
    ),
    (
        "Python traceback Spanish acento",
        r"^\s*Archivo\s\".*\",\slínea\s[0-9]+",
        r"^\s*Archivo\s\"(.*)\",\slínea\s([0-9]+)",
    ),
    (
        "Python traceback 2 Spanish",
        r"^\s*.*\:\slinea\s[0-9]+",
        r"^\s*(.*)\:\slinea\s([0-9]+)",
    ),
    (
        "Python traceback 2 Spanish acento",
        r"^\s*.*\:\slínea\s[0-9]+",
        r"^\s*(.*)\:\slínea\s([0-9]+)",
    ),
    ("Python pytest report", r"^\s.*\:\:[a-zA-Z0-9\_]+\s", r"^\s*(.*\:\:[a-zA-Z0-9\_]+)\s",),
    (
        "line starts by 'ERROR in Filename:line' pattern (GCC/make). File path should exists.",
        r"\s.\S[^\s\s].[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:[0-9]+",
        r"\s.\S[^\s\s].(.*)\:([0-9]+)",
    ),
    (
        "line starts by 'Filename:line' pattern (GCC/make). File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:[0-9]+",
        r"^\s*(.*)\:([0-9]+)",
    ),
    (
        "line starts by 'Filename: line 43:' pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\ line\ [0-9]\:+",
        r"^\s*(.*)\:\ \l\i\n\e\ ([0-9]+)\:",
    ),
    (
        "line starts by 'Filename: line 43:a' 2 pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\s\w\s[0-9]\:+",
        r"^\s*(.*)\:\s\w\s([0-9]+)\:",
    ),
    (
        "line starts by 'Filename: line 43:' 3 pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\sline\s[0-9]\:+",
        r"^\s*(.*)\:\sline\s([0-9]\:+)",
    ),
    (
        "line starts by 'Filename: line 43:' 4 pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\sline\s[0-9]+",
        r"^\s*(.*)\:\sline\s([0-9]+)",
    ),
    (
        "line starts by 'archivo: linea 43:' pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\slinea\s[0-9]\:+",
        r"^\s*(.*)\:\slinea\s([0-9]\:+)",
    ),
    (
        "line starts by 'archivo: linea 432:' pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\slinea\s[0-9]+",
        r"^\s*(.*)\:\slinea\s([0-9]+)",
    ),
    (
        "line starts by 'archivo: línea 43:' acento pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\slínea\s[0-9]\:+",
        r"^\s*(.*)\:\slínea\s([0-9]\:+)",
    ),
    (
        "line starts by 'archivo: línea 432:' acento pattern Bash. File path should exists.",
        r"^\s*[a-zA-Z0-9\/\_\-\.\ ]+\.?[a-zA-Z0-9]+\:\slínea\s[0-9]+",
        r"^\s*(.*)\:\slínea\s([0-9]+)",
    ),
]

# Transparency max level (should be always 100)
MAX_TRANSPARENCY = 100

# Tabs session schema version
TABS_SESSION_SCHEMA_VERSION = 2

# Constants for vte regex matching are documented in the pcre2 api:
#   https://www.pcre.org/current/doc/html/pcre2api.html
PCRE2_MULTILINE = 0x00000400
