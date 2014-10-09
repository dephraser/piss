# -*- coding: utf-8 -*-

import os
from piss import PISS


# Grab the paths for the Eve settings file and the instance folder
settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')
instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')

# Initialize the app
app = PISS(settings=settings_file,
          instance_path=instance_path)

if __name__ == '__main__':
    app.run()
