# -*- coding: utf-8 -*-

import os
import json
from eve import Eve
from cerberus import Validator
from flask.config import Config
from .utils import NewBase60Encoder, NewBase60Validator
from .auth import HawkAuth
from .event_hooks import before_insert_posts, before_update_posts, \
    after_fetched_item_posts, before_GET_posts, before_POST_posts, \
    after_POST_posts
from .services import attachments, server_info, syndication
from .eve_override import eve_override


def PISS(instance_path):
    # Create a configuration object and read the configuration file
    app_config = Config(instance_path)
    app_config.from_pyfile('piss.cfg')

    # If `EVE_SETTINGS` exists and points to valid file, use that instead of
    # the default `settings.py`
    alt_settings = app_config.get('EVE_SETTINGS', None)
    if alt_settings and os.path.isfile(alt_settings):
        settings_file = alt_settings
    else:
        settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')

    # Create the app instance
    app = Eve(settings=settings_file, 
              json_encoder=NewBase60Encoder, 
              validator=NewBase60Validator,
              auth=HawkAuth,
              instance_path=instance_path,
              static_folder=None)

    # Update the app's config object with our settings
    app.config.update(**dict(app_config))

    # Add event hooks
    app.on_insert_posts += before_insert_posts
    app.on_update_posts += before_update_posts
    app.on_fetched_item_posts += after_fetched_item_posts
    app.on_pre_GET_posts += before_GET_posts
    app.on_pre_POST_posts += before_POST_posts
    app.on_post_POST_posts += after_POST_posts

    # Make sure necessary settings exist
    missing_settings = []
    for setting in ('META_POST', 'ROOT_CREDENTIALS', 'SECRET_KEY', 'MENU_ITEMS', 'SERVER_NAME'):
        if not app.config.get(setting, None):
            missing_settings.append(setting)
    if missing_settings:
        raise SystemExit('Missing configuration settings! (%s)' % (','.join(missing_settings),))

    # Check that a `meta.json` file exists in `types` and that you can read from it
    meta_schema = ''
    meta_schema_file = os.path.join(os.path.dirname(instance_path), 'types/meta.json')
    try:
        with open(meta_schema_file, 'r') as f:
            meta_schema = f.read()
    except IOError as e:
        raise SystemExit('Could not find `meta` post schema file at %s!' % (meta_schema_file,))
    if not meta_schema:
        raise SystemExit('No data in `meta` post schema at %s!' % (meta_schema_file,))

    # Validate the data in `META_POST` against the `meta` post schema
    v = Validator(json.loads(meta_schema))
    if not v.validate(app.config['META_POST']):
        raise SystemExit('Invalid `META_POST` configuration! \
            Validator returned the following errors: \n%s' % (str(v.errors),))

    # Make sure necessary directories exist
    if not os.path.isdir(os.path.join(instance_path, 'attachments')):
        os.makedirs(os.path.join(instance_path, 'attachments'))
    if not os.path.isdir(os.path.join(instance_path, 'tmp')):
        os.makedirs(os.path.join(instance_path, 'tmp'))

    # Add some additional services besides the REST API
    app.register_blueprint(attachments)
    app.register_blueprint(server_info)
    app.register_blueprint(syndication)

    # Override some of Eve's default methods in order to also handle HTML requests
    eve_override(app)
    
    return app
