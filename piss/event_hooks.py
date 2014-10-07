# -*- coding: utf-8 -*-

import os
import time
import hashlib
import json
from eve.methods.post import post_internal
from eve.render import send_response
from flask import current_app, request, abort
from hawk.hcrypto import random_string
from .utils import NewBase60, get_post_by_id


def before_posts_insert(documents):
    meta_post = current_app.config.get('META_POST')
    types_endpoint = meta_post['server']['urls']['types']
    posts_endpoint = meta_post['server']['urls']['posts_feed']
    
    for document in documents:
        # Create version information, but save app version data if present
        current_time = time.time()
        time_seconds = int(current_time)
        time_millisec = int(current_time * 1000)
        time_microsec = int(current_time * 1000000)
        app_version = get_app_version(document)
        digest = create_version_digest(document)
        document['version'] = create_version_document(digest, time_millisec, app_version)
        
        # Create an ID for the document
        if document['type'] == (types_endpoint + '/credentials'):
            # Since credentials posts are created automatically by the server,
            # we need to specify their IDs in microseconds
            document['_id'] = str(NewBase60(time_microsec))
        else:
            document['_id'] = str(NewBase60(time_seconds))
        
        # Additional processing for certain post types
        if document['type'] == (types_endpoint + '/app'):
            # For app posts, we must create an additional credentials post
            # and make sure they link to each other
            credentials_post = {
                'entity': str(meta_post['entity']),
                'type': str(types_endpoint + '/credentials'),
                'content': {
                    'hawk_key': str(random_string(64)),
                    'hawk_algorithm': 'sha256'
                },
                'links': [
                    {
                        'post': str(document['_id']),
                        'url': str(posts_endpoint + "/" + document['_id']),
                        'type': str(types_endpoint + '/app')
                    }
                ]
            }
            response, _, _, status = post_internal('posts', credentials_post)
            document['links'] = [
                {
                    'post': str(response['_id']),
                    'url': str(posts_endpoint + "/" + response['_id']),
                    'type': str(types_endpoint + '/credentials')
                }
            ]

def before_posts_post(request):
    '''
    Callback to be executed before documents have been validated. Primarily used
    to handle multipart form data.
    '''
    if request.mimetype == 'multipart/form-data':
        payload = {}
        attachments_path = os.path.join(current_app.instance_path, 'attachments')
        for key in request.form:
            payload = json.loads(request.form[key])
        for key in request.files:
            file = request.files[key]
            file.save(os.path.join(attachments_path, file.filename))
        response = post_internal('posts', payload)
        abort(send_response('posts', response))

def after_posts_post(request, payload):
    '''
    Callback to be executed after documents have been inserted into the 
    database. Primarily used to change the response envelope depending on the
    post type.
    '''
    meta_post = current_app.config.get('META_POST')
    types_endpoint = meta_post['server']['urls']['types']
    
    # TODO: Code below needs to account for when the payload is a list
    if payload.status_code == 201:
        payload_data = json.loads(payload.get_data())
        if payload_data['type'] == str(types_endpoint + "/app"):
            payload_id = payload_data['_id']
            app_post = get_post_by_id(payload_id)
            app_links = app_post['links']
            for link in app_links:
                if link['type'] == str(types_endpoint + "/credentials"):
                    payload.headers['Link'] = '<%s>; rel="%s"' % (link['url'], str(types_endpoint + "/credentials"))
                    break

def before_posts_update(updates, original):
    # Create an updated version of the original *without* the `version` field,
    # but save app version data if present
    current_time = int(time.time())
    app_version = get_app_version(updates)
    updated = original.copy()
    updated.update(updates)
    try:
        del(updated['version'])
    except KeyError as e:
        # Weird that it didn't have it, but just as well
        pass
    
    # Create version information and append it to the updates
    digest = create_version_digest(updated)
    updates['version'] = create_version_document(digest, current_time, app_version)

def before_posts_get(request, lookup):
    '''
    Before performing a GET request, check the authorization headers. If no
    auth headers are found or the auth is an incorrect type, set the lookup to
    find only public posts.
    '''
    http_auth = request.headers.get('Authorization')
    bewit_query = request.args.get('bewit')
    if not http_auth and not bewit_query:
        lookup['permissions'] = {'public': True}

# -----------------------------------------------------------------------------
# Event hook utilities
# -----------------------------------------------------------------------------

def create_version_digest(document):
    hasher = hashlib.sha512()
    hasher.update(str(document))
    # Hex-encoded first 256 bits of the SHA-512
    return hex(int(hasher.hexdigest(), 16) >> 256)

def create_version_document(digest, current_time, app_version):
    version_document = {}
    version_document['id'] = digest
    
    # The following values mirror the schema in settings.py
    if 'published_at' in app_version:
        version_document['published_at'] = app_version['published_at']
    else:
        version_document['published_at'] = current_time * 1000
    if 'parents' in app_version:
        version_document['parents'] = app_version['parents']
    if 'message' in app_version:
        version_document['message'] = app_version['message']
    if 'delta' in app_version:
        version_document['delta'] = app_version['delta']
    
    return version_document

def get_app_version(document):
    app_version = {}
    if 'version' in document:
        app_version = document['version']
        del(document['version'])
    return app_version