#!/bin/env bash

function main(){
# guake --quit     This just starts the terminal to later stop it. 

pkill guake                                                        # incase is running in the background
source env/bin/activate     # Go into your virtualenv environment
make
sudo make dev               # build with sudo to warranty a clean build
source deactivate           # Get out of your virtualenv environment
sudo make install           # install with sudo to replace your current executables
guake --show --verbose      # or in case you also want to see what is going on.
}

time main
