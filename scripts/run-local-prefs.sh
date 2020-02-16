#!/bin/bash

echo "execute Guake GTK3 for developer."

VIRTUALENV_PATH=$(poetry env info --path)

source $VIRTUALENV_PATH/bin/activate

bash <<EOF
python 2>/dev/null <<EOC
import gi
EOC
if [ \$? -eq 1 ]; then
    pew toggleglobalsitepackages
fi
PYTHONPATH=. python3 guake/main.py --no-startup-script -p
echo "Done"
EOF
