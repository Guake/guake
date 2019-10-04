from __future__ import print_function
import site, os
prefix=os.getenv("PREFIX")
for d in site.getsitepackages(None if not prefix else [prefix]):
    print(d)
