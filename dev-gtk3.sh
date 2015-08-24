#!/bin/bash

echo "execute Guake GTK3 for developer."

sudo ./install.py

PYTHONPATH=src-gtk3 python3 src-gtk3/guake/gtk3test.py
