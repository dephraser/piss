# -*- coding: utf-8 -*-

import os
import json
from twython import Twython
from flask import Blueprint, jsonify, current_app, make_response, render_template, send_from_directory, abort, request
from eve.methods import getitem
from eve.methods.patch import patch_internal
from eve.render import render_xml
from .utils import get_post_by_id, request_is_json, request_is_xml
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

@services.route('/syndicate/<service>', methods=['POST'])
def syndicate(service):
    '''
    Syndicate a post to the given service. Checks if the original post exists
    and if it hasn't been syndicated to the given service already.
    '''
    # TODO: All of this stuff will probably end up living it its own file at
    # `piss/syndication/twitter.py`
    if service.lower() == 'twitter':
        # Get the Twitter configuration
        tw_conf = current_app.config.get('TWITTER', None)
        if not tw_conf:
            abort(400, '%s not configured on the server.' % service.lower().capitalize())
        # TODO: We should probably abort if the `Content-Type` isn't
        # `application/json`
        data = request.json
        entity = 'https://twitter.com/'
        meta_post = current_app.config.get('META_POST')
        post_type = os.path.join(meta_post['entity'], 'types', 'note')
        # TODO: below would be better as a Cerberus validation
        if not data['entity'] == entity:
            abort(422, 'Incorrect entity for %s service.' % service)
        if not data['type'] == post_type:
            abort(422, 'Incorrect post type for %s service.' % service)
        if 'post' not in data['links'][0]:
            abort(422, 'Post ID not specified.')
        if 'content' not in data or 'text' not in data['content']:
            abort(422, 'Post content not found!')
        # Get the post we want to syndicate
        post_id = data['links'][0]['post']
        post = get_post_by_id(post_id)
        if not post:
            abort(404)
        # Grab the existing links from the post, if any
        links = []
        if 'links' in post:
            links = post['links']
            for link in links:
                if link['entity'] == entity and link['type'] == 'syndication':
                    abort(400, 'Post ID %s already syndicated to %s.' % (post_id, service))
        # Create the twitter status and grab the permalink
        twitter = Twython(tw_conf['app_key'], tw_conf['app_secret'], tw_conf['token'], tw_conf['token_secret'])
        status = twitter.update_status(status=data['content']['text'])
        url = os.path.join(entity, status['user']['screen_name'], 'status', status['id_str'])
        # Append the syndication link and `PATCH` the original post
        links.append({'entity': entity, 'type': 'syndication', 'url': url})
        response, _, _, status = patch_internal('posts', {'links': links}, concurrency_check=False, **{'_id': post_id})
        if status in (200, 201):
            return render_object_response(response, 'item.html', title="Syndicate to %s" % (service.lower().capitalize(),))
        abort(status)
    abort(400, 'Service not recognized.')

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
