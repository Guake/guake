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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import signal
import logging
import sys

from guake.logging import setupBasicLogging
from guake.logging import setupLogging

from guake.application import GuakeApplication

logger = logging.getLogger(__name__)


def main():
    setupBasicLogging()
    setupLogging()
    logger.info("Guake starts")
    app = GuakeApplication()
    # Trick to handle KeyboardInterrupt
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.run()

if __name__ == '__main__':
    main()
