#!/bin/env bash

function main(){
# guake --quit     This just starts the terminal to later stop it. 
pkill guake     
pipenv --rm                                                 # incase is running in the background
source env/bin/activate     # Go into your virtualenv environment
make
make dev               # build with sudo to warranty a clean build
 make test               # build with sudo to warranty a clean build
source deactivate           # Get out of your virtualenv environment
}

time main
