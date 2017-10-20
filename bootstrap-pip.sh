#!/bin/bash

echo "Freeze version of pip to ensure reproductibility"

sudo -E pip install -U  'pip==9.0.1' \
                'pipenv==8.2.7' \
                'setuptools==36.6.0' \
    || echo "you may need to sudo me !"
