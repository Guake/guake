# -*- coding: utf-8 -*-

import setuptools

# Only kept because the Makefile still runs `python setup.py ...`. All configuration
# lives in pyproject.toml; setuptools_scm comes from the dev environment (Pipfile)
# for these direct calls, and from [build-system].requires for pip / build.
setuptools.setup()
