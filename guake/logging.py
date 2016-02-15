from __future__ import absolute_import

import logging


def setupBasicLogging():
    fmt = '%(asctime)-15s %(levelname)6s %(message)s'
    logging.basicConfig(format=fmt, level=logging.INFO)


def setupLogging():
    config_file_fullpath = ""
    logging.config.fileConfig(config_file_fullpath)
