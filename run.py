# -*- coding: utf-8 -*-

import os
from eve import Eve
from piss.utils import NewBase60Encoder, NewBase60Validator
from piss.auth import HawkAuth
from piss.event_hooks import before_insert, before_update, pre_posts_get_callback, after_posts_insert
from html_renderer import HTML_Renderer, HTML_STATIC_FOLDER


# Grab the paths for the Eve settings file and the instance folder
settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')
instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')

# Initialize the app
app = Eve(settings=settings_file, 
          json_encoder=NewBase60Encoder, 
          validator=NewBase60Validator,
          auth=HawkAuth,
          instance_path=instance_path,
          static_folder=HTML_STATIC_FOLDER)

# Add event hooks
app.on_insert += before_insert
app.on_update += before_update
app.on_pre_GET_posts += pre_posts_get_callback
app.on_post_POST_posts += after_posts_insert

# Load some instance configuration settings
app.config.from_pyfile(os.path.join(instance_path, 'piss.cfg'))

# Add the HTML renderer
HTML_Renderer(app)

if __name__ == '__main__':
    app.run()
