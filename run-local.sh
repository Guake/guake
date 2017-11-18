#!/bin/bash

echo "execute Guake GTK3 for developer."

# Hack to find the virtualenv path
VIRTUALENV_PATH=$(export | grep ' PATH=' | cut -d'=' -f2 | cut -d':' -f1 | sed 's/\/bin$//' | sed 's/^"//')

source $VIRTUALENV_PATH/bin/activate
# Hack to enable global site packages (pipenv does not provide this feature)
bash <<EOF
python 2>/dev/null <<EOC
import gi
EOC
if [ \$? -eq 1 ]; then
    pew toggleglobalsitepackages
fi
guake --no-startup-script
echo "Done"
EOF
