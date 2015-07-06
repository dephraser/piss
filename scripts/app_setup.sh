#!/usr/bin/env bash

# Get the directory we're working from
if [ -d /home/vagrant/sync ]; then
    DIR="/home/vagrant/sync"
else
    DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
fi

# Make sure we're in the right directory
cd $DIR

# Create a virtual environment with the correct Python version
virtualenv -p `which python2.7` venv
. venv/bin/activate
pip install -r requirements.txt
python run.py &

