# -*- coding: utf-8 -*-

import os
from eve import Eve
from piss.utils import NewBase60Encoder, NewBase60Validator
from piss.auth import HawkAuth
from piss.event_hooks import before_posts_insert, before_posts_update, before_posts_get, before_posts_post, after_posts_post
from piss.routes import server
from piss.html_renderer import HTML_Renderer


# Grab the paths for the Eve settings file and the instance folder
settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')
instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')

# Initialize the app
app = Eve(settings=settings_file, 
          json_encoder=NewBase60Encoder, 
          validator=NewBase60Validator,
          auth=HawkAuth,
          instance_path=instance_path)

# Add event hooks
app.on_insert_posts += before_posts_insert
app.on_update_posts += before_posts_update
app.on_pre_GET_posts += before_posts_get
app.on_pre_POST_posts += before_posts_post
app.on_post_POST_posts += after_posts_post

# Load some instance configuration settings
app.config.from_pyfile(os.path.join(instance_path, 'piss.cfg'))

# Make sure necessary settings exist
missing_settings = []
for setting in ('META_POST', 'ROOT_CREDENTIALS', 'SECRET_KEY', 'MENU_ITEMS'):
    if not app.config.get(setting, None):
        missing_settings.append(setting)
if missing_settings:
    raise SystemExit('Missing configuration settings! (%s)' % (','.join(missing_settings),))

# Make sure necessary directories exist
if not os.path.isdir(os.path.join(app.instance_path, 'attachments')):
    os.makedirs(os.path.join(app.instance_path, 'attachments'))
if not os.path.isdir(os.path.join(app.instance_path, 'tmp')):
    os.makedirs(os.path.join(app.instance_path, 'tmp'))

# Add some routes
app.register_blueprint(server)

# Add the HTML renderer
HTML_Renderer(app)

if __name__ == '__main__':
    app.run()
