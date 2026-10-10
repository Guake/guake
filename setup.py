# -*- coding: utf-8 -*-

import setuptools

# setup_requires + use_scm_version keep `python setup.py ...` (used by the
# Makefile) working without build isolation; the setuptools_scm settings
# themselves live in pyproject.toml under [tool.setuptools_scm].
setuptools.setup(setup_requires=["setuptools_scm>=8,<9"], use_scm_version=True)
