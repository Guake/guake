#!/bin/bash

cd src
export PYTHONPATH=.:globalhotkeys/.libs
python tests/test_quit_edit.py

