# -*- coding: utf-8 -*-

import os
import json
from flask import Blueprint, jsonify, current_app, make_response, render_template, send_from_directory, abort, request
from eve.methods import getitem
from eve.render import render_xml
from .utils import request_is_json, request_is_xml
from .attachments import get_attachment_dir

services = Blueprint('services', __name__)

@services.route('/meta')
def meta():
    '''
    Return the `meta` post for the server. Checks the `Accept` header to 
    return a response of the appropriate type.
    '''
    return render_object_response(current_app.config['META_POST'], 'item.html', title='Meta')

@services.route('/types')
def types_resource():
    types_dir = os.path.join(os.path.dirname(current_app.instance_path), 'types')
    files = []
    for (_, _, filenames) in os.walk(types_dir):
        files.extend(filenames)
        break
    items = []
    for file in files:
        items.append({'_id': file.split('.')[0]})
    return render_object_response(items, 'items.html', feed_url='%s/types' % (current_app.config['META_POST']['entity'],))

@services.route('/types/<name>')
def types_item(name):
    types_dir = os.path.join(os.path.dirname(current_app.instance_path), 'types')
    type_file = name + '.json'
    type_schema = ''
    try:
        with open(os.path.join(types_dir, type_file), 'r') as f:
            type_schema = f.read()
    except Exception as e:
        abort(404)
    type_schema = json.loads(type_schema)
    return render_object_response(type_schema, 'item.html', title="Type: %s" % (name.capitalize(),))

@services.route('/attachments/<digest>')
def attachments(digest):
    '''
    Given an attachment digest, find a post that lists the digest in its 
    `attachments` array and return the relevant file.
    '''
    lookup = {
        'attachments': {
            '$elemMatch': {
                'digest': digest
            }
        }
    }
    attachment = get_attachment('digest', digest, lookup)
    return send_from_directory(get_attachment_dir(digest), digest, mimetype=attachment['content_type'])

@services.route('/posts/<pid>/<name>')
def post_attachment(pid, name):
    '''
    Given a post ID and file name, retrieve the post, find the matching 
    attachment, and return the relevant file.
    '''
    attachment = get_attachment('name', name, {'_id': pid})
    digest = attachment['digest']
    return send_from_directory(get_attachment_dir(digest), digest, mimetype=attachment['content_type'])

def get_attachment(key, value, lookup):
    '''
    Performs a lookup for a particular post and returns an attachment document 
    if one of its keys matches the given value. Also makes sure to reject
    `version` requests that would be impossible to fulfill.
    '''
    if 'version' in request.args and request.args['version'] in ('all', 'diffs'):
        abort(400)
    post, _, _, _ = getitem('posts', lookup)
    if not post:
        abort(404)
    for attachment in post['attachments']:
        if attachment[key] == value:
            break
    else:
        # We never found a matching digest -- abort
        abort(404)
    return attachment

def render_object_response(obj, template_name, **kwargs):
    '''
    Converts a Python object into a suitable response object (JSON, XML, or 
    HTML) depending on the `Accept` header of the request.
    '''
    if request_is_json():
        if not isinstance(obj, dict):
            obj = {'_items': obj}
        return jsonify(obj)
    elif request_is_xml():
        response = make_response(render_xml(obj))
        response.mimetype = 'application/xml'
        response.charset = 'utf-8'
        return response
    else:
        return render_template(template_name, obj=obj, **kwargs)
