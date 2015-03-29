# -*- coding: utf-8 -*-

'''
Facebook

Handlers for interacting with the Facebook API.

# Facebook SDK
Initialize the graph object:

    graph = facebook.GraphAPI(access_token)

Get the user:

    user = graph.get_object("me")

See what permissions are available:

    graph.request('/%s/permissions' % user['id'])

'''

import os
import time
import urllib
import cgi
import requests
import facebook
from flask import abort, current_app
from piss.utils import get_post_by_id
from .utils import is_duplicate_syndication, validate_service

FACEBOOK_ENTITY = 'https://www.facebook.com/'
SCOPE = 'publish_actions,rsvp_event,user_actions.news,user_actions.video,user_events,user_friends,user_likes,user_location,user_photos,user_status,user_tagged_places,user_videos,user_groups,read_friendlists,read_mailbox,read_stream,manage_notifications'


def facebook_handler(data, server_entity):
    '''
    Syndicates request data to Facebook.

    :param data: request data with syndication information.
    :param server_entity: the entity we are syndicating for.
    '''
    post_type = os.path.join(server_entity, 'types', 'note')
    errors = validate_service(data, FACEBOOK_ENTITY, post_type)
    if errors:
        abort(422, ' '.join(errors))
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
    if is_duplicate_syndication(links, FACEBOOK_ENTITY):
        abort(400, 'Post ID %s already syndicated to Facebook.' % (post_id,))
    # Grab information for attachments, if any. Make sure they're only the kind
    # that Twitter accepts and use only the first 4.
    attachments = []
    if 'attachments' in post:
        attachments = post['attachments']
    attachments = [x for x in attachments if x['content_type']\
                   in ('image/gif', 'image/jpeg', 'image/png')]
    if len(attachments) > 1:
        attachments = attachments[0:1]
    if attachments:
        attachments = [os.path.join(server_entity,
                                    post['_links']['self']['href'],
                                    x['name']) for x in attachments]
    # Create the Facebook status and grab the permalink
    try:
        url = create_status_post(data['content']['text'], attachments)
    except facebook.GraphAPIError as e:
        abort(400, str(e))
    # Append the syndication link and `PATCH` the original post
    links.append({'entity': FACEBOOK_ENTITY, 'type': 'syndication',
                 'url': url})
    return (post_id, links)


def create_status_post(message, attachments=None):
    '''
    Create a Facebook status post.

    :param status: the text of the Facebook post.
    :param attachments: optional list of URLs to media attachments.
    :returns: permalink to the status post.
    '''
    # Get the Facebook configuration
    fb_conf = current_app.config.get('FACEBOOK', None)
    if not fb_conf:
        abort(400, 'Facebook not configured on the server.')
    data = {'message': message}
    edge = 'feed'
    r_key = 'id'
    if attachments:
        edge = 'photos'
        data['url'] = attachments[0]
        r_key = 'post_id'
    graph = facebook.GraphAPI(fb_conf['access_token'])
    response = graph.put_object("me", edge, **data)
    user_id, post_id = response[r_key].split('_')
    url = 'https://www.facebook.com/%s/posts/%s' % (user_id, post_id)
    return url


def oauth_authorize(client_id, redirect_uri):
    '''
    Return the URL of a page that will let the user authorize permissions for
    the app.
    '''
    args = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': SCOPE
    }
    return 'https://graph.facebook.com/oauth/authorize?%s' % urllib.urlencode(args)


def oauth_access_token(client_id, client_secret, code, redirect_uri):
    '''
    Given an authorization code, get the access token.
    '''
    args = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code': code
    }
    response = requests.get('https://graph.facebook.com/oauth/access_token?%s' % urllib.urlencode(args))
    data = cgi.parse_qs(response.text)
    return (data['access_token'][0], int(time.time()) + int(data['expires'][0]))
