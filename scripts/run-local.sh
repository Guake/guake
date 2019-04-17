#!/bin/bash

echo "execute Guake GTK3 for developer."

if test "$1" == "-v"; then
	VERBOSE="-v";
fi

VIRTUALENV_PATH=$(pipenv --venv)

source $VIRTUALENV_PATH/bin/activate

bash <<EOF
python 2>/dev/null <<EOC
import gi
EOC
if [ \$? -eq 1 ]; then
    pew toggleglobalsitepackages
fi
PYTHONPATH=. python3 guake/main.py --no-startup-script $VERBOSE
echo "Done"
EOF
