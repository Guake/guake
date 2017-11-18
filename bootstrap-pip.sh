#!/bin/bash

echo "Freeze version of pip to ensure reproductibility"

pip install --user --upgrade \
    'pip==9.0.1' \
    'pipenv==8.3.2' \
    'setuptools==36.6.0' \
    || echo "you may need to sudo me !"

echo "Please ensure your local bin directory is in your path"
echo "Linux: export PATH=$HOME/.local/bin$PATH"
