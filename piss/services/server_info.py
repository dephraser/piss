# -*- coding: utf-8 -*-

import os
import json
from flask import Blueprint, current_app
from .utils import render_response

server_info = Blueprint('server_info', __name__)

@server_info.route('/meta')
def meta():
    '''
    Return the `meta` post for the server. Checks the `Accept` header to 
    return a response of the appropriate type.
    '''
    return render_response(current_app.config['META_POST'], 'item.html',
                           title='Meta')


@server_info.route('/types')
def types_resource():
    '''
    Return a list of post types available on the server.
    '''
    types_dir = os.path.join(os.path.dirname(current_app.instance_path),
                                             'types')
    files = []
    for (_, _, filenames) in os.walk(types_dir):
        files.extend(filenames)
        break
    items = []
    for file in files:
        items.append({'_id': file.split('.')[0]})
    return render_response(items, 'items.html', feed_url='%s/types'
                           % (current_app.config['META_POST']['entity'],))


@server_info.route('/types/<name>')
def types_item(name):
    '''
    Return the schema for a given post type.

    :param name: the name of the post type to be displayed.
    '''
    types_dir = os.path.join(os.path.dirname(current_app.instance_path), 'types')
    type_file = name + '.json'
    type_schema = ''
    try:
        with open(os.path.join(types_dir, type_file), 'r') as f:
            type_schema = f.read()
    except Exception as e:
        abort(404)
    type_schema = json.loads(type_schema)
    return render_response(type_schema, 'item.html',
                           title="Type: %s" % (name.capitalize(),))