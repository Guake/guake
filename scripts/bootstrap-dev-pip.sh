#!/bin/bash

echo "Freeze version of pip to ensure build reproductibility"

if [[ $1 == "system" ]]; then
    op=""
else
    op="--user "
fi

python3 -m pip install $op --upgrade \
    'pip==24.3.1' \
    'pipenv==2024.4.0' \
    || echo "you may need to sudo me !"

echo "Please ensure your local bin directory is in your path"
echo "Linux: export PATH=$HOME/.local/bin:$PATH"
