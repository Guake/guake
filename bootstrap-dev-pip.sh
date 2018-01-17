#!/bin/bash

echo "Freeze version of pip to ensure build reproductibility"

if [[ $1 == "system" ]]; then
    op=""
else
    op="--user "
fi

python3 -m pip install $op --upgrade \
    'pip==9.0.1' \
    'pipenv==9.0.1' \
    'setuptools==36.6.0' \
    || echo "you may need to sudo me !"

echo "Please ensure your local bin directory is in your path"
echo "Linux: export PATH=$HOME/.local/bin$PATH"
