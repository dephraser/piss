# -*- coding: utf-8 -*-

import time
import hashlib
import json
from eve.methods.post import post_internal
from eve.render import send_response
from flask import current_app, request, abort, url_for, Response, g
from hawk.hcrypto import random_string
from hawk.client import get_bewit as hawk_get_bewit
from .utils import NewBase60, is_collection_request
from .attachments import save_attachment

# Bewits are good for 1 hour
BEWIT_TTL = 60 * 60

def before_insert_posts(documents):
    meta_post = current_app.config.get('META_POST')
    posts_endpoint = meta_post['server']['urls']['posts_feed']
    app_type = str(url_for('services.types_item', name='app', _external=True))
    credentials_type = str(url_for('services.types_item', name='credentials', _external=True))
    
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
        if document['type'] == credentials_type:
            # Since credentials posts are created automatically by the server,
            # we need to specify their IDs in microseconds
            document['_id'] = str(NewBase60(time_microsec))
        else:
            document['_id'] = str(NewBase60(time_seconds))
        
        # Additional processing for certain post types
        if document['type'] == app_type:
            # For app posts, we must create an additional credentials post
            # and make sure they link to each other
            hawk_key = str(random_string(64))
            hawk_algorithm = 'sha256'
            credentials_post = {
                'entity': str(meta_post['entity']),
                'type': credentials_type,
                'content': {
                    'hawk_key': hawk_key,
                    'hawk_algorithm': hawk_algorithm
                },
                'links': [
                    {
                        'post': str(document['_id']),
                        'url': str(posts_endpoint + "/" + document['_id']),
                        'type': app_type
                    }
                ]
            }
            response, _, _, status = post_internal('posts', credentials_post)
            if not 'links' in document:
                document['links'] = []
            cred_id = str(response['_id'])
            cred_url = str(posts_endpoint + "/" + cred_id)
            document['links'].append({
                    'post': cred_id,
                    'url': cred_url,
                    'type': credentials_type
                })
            # Create a signal to change the POST response envelope
            g.app_POST = True
            credentials = {
                'id': cred_id,
                'key': hawk_key,
                'algorithm': hawk_algorithm
            }
            g.cred_bewit_url = cred_url + '?bewit=' + hawk_get_bewit(cred_url, {'credentials': credentials, 'ttl_sec': BEWIT_TTL})

def before_update_posts(updates, original):
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

def after_fetched_item_posts(response):
    '''
    Inspect an item after it has been fetched and reject the request if a 
    non-authorized request has been made on a private post.
    '''
    if getattr(g, 'non_authed_GET', False):
        if '_items' in response:
            if request.args.get('version', '') == 'diffs':
                # Diffs may omit the permissions document if it has never
                # changed, so we can't show them on public requests
                abort(400, description="Version diffs not supported for unauthenticated requests.")
            # Respect the permissions of the latest version
            if not is_public_post(response['_items'][len(response['_items']) - 1]):
                authenticate()
        else:
            if not is_public_post(response):
                authenticate()

def before_POST_posts(request):
    '''
    Callback to be executed before documents have been validated. Primarily used
    to handle multipart form data.
    '''
    if request.mimetype == 'multipart/form-data':
        # This is designed to parse only a single `request.form` item. 
        # Additional items will be ignored.
        payload = {}
        for key in request.form:
            payload = json.loads(request.form[key])
            break
        
        # The actual names of the keys used to send `request.files` data are
        # ignored.
        attachments = []
        for key in request.files:
            file = request.files[key]
            attachments.append(save_attachment(file))
        
        if attachments:
            payload['attachments'] = attachments
        response = post_internal('posts', payload)
        
        # Instead of continuing with the default response (where the request 
        # will be sent to Eve's `post` function), we abort normal operation and
        # create our own response.
        abort(send_response('posts', response))

def after_POST_posts(request, payload):
    '''
    Callback to be executed after documents have been inserted into the 
    database. Primarily used to change the response envelope depending on the
    post type.
    '''
    meta_post = current_app.config.get('META_POST')
    
    # TODO: Code below needs to account for when the payload is a list
    if payload.status_code == 201 and getattr(g, 'app_POST', False):
        link_header = ''
        credentials_type = str(url_for('services.types_item', name='credentials', _external=True))
        if 'Link' in payload.headers:
            link_header = '%s,' % (payload.headers['Link'],)
        payload.headers['Link'] = link_header + '<%s>; rel="%s"' % (getattr(g, 'cred_bewit_url'), credentials_type)

def before_GET_posts(request, lookup):
    '''
    If an non-authorized request is being attempted on a collection, set the 
    lookup to find only public posts.
    '''
    if getattr(g, 'non_authed_GET', False) and is_collection_request(request):
        lookup['permissions'] = {'public': True}
                

# -----------------------------------------------------------------------------
# Event hook utilities
# -----------------------------------------------------------------------------

def authenticate():
    '''
    Copied from Eve's `BasicAuth` class. Used as a final layer of defense when
    a non-authenticated request to a private resource is made.
    '''
    resp = Response(None, 401, {'WWW-Authenticate': 'Basic realm:"%s"' %
                                __package__})
    abort(401, description='Please provide proper credentials',
          response=resp)

def is_public_post(post):
    '''
    Test to see if a post is marked as public.
    '''
    return 'permissions' in post and post['permissions'].get('public', False)

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