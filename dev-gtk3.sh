#!/bin/bash

echo "execute Guake GTK3 for developer."

#sudo ./install.py

PYTHONPATH=src python3 src/guake/main.py --no-startup-script
