from .application import GuakeApplication

from guake.logging import setupBasicLogging
from guake.logging import setupLogging




def guakeInit():
    setupBasicLogging()
    setupLogging()
