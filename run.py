#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from piss import PISS


# Grab the path for the instance folder
instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')

# Initialize the app
app = PISS(instance_path=instance_path)

if __name__ == '__main__':
    app.run()
