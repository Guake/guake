from __future__ import print_function

import os
import site

prefix = os.getenv("PREFIX")
for d in site.getsitepackages(None if not prefix else [prefix]):
    print(d)
