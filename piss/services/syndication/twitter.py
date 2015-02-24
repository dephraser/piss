# -*- coding: utf-8 -*-

'''
Twitter

Handlers for interacting with the Twitter API.

Example `curl` command:

```
curl -XPOST -H 'Content-Type: application/json' -H 'Accept: application/json'
http://localhost:5000/syndicate/twitter -d '{"entity":"https://twitter.com/",
"type":"http://localhost:5000/types/note", "content":{"text":"Testing..."}, 
"links":[{"post":"1p2H0e"}]}'
```

'''

import os
from twython import Twython, TwythonError
from flask import abort, current_app
from piss.file_io import get_attachment_file
from piss.utils import get_post_by_id
from .utils import is_duplicate_syndication, validate_service

TWITTER_ENTITY = 'https://twitter.com/'


def twitter_handler(data, server_entity):
    '''
    Syndicates request data to Twitter.

    :param data: request data with syndication information.
    :param server_entity: the entity we are syndicating for.
    '''
    tw_conf = current_app.config.get('TWITTER', None)
    if not tw_conf:
        abort(400, 'Twitter not configured on the server.')
    tw = Twython(tw_conf['app_key'], tw_conf['app_secret'],
                 tw_conf['token'], tw_conf['token_secret'])
    post_type = os.path.join(server_entity, 'types', 'note')
    errors = validate_service(data, TWITTER_ENTITY, post_type)
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
    if is_duplicate_syndication(links, TWITTER_ENTITY):
        abort(400, 'Post ID %s already syndicated to Twitter.' % (post_id,))
    # Grab information for attachments, if any. Make sure they're only the kind
    # that Twitter accepts and use only the first 4.
    attachments = []
    if 'attachments' in post:
        attachments = post['attachments']
    attachments = [x for x in attachments if x['content_type']\
                   in ('image/gif', 'image/jpeg', 'image/png')]
    if len(attachments) > 4:
        attachments = attachments[0:3]
    media_ids = []
    try:
        for attachment in attachments:
            media_id = upload_media(tw,
                                    get_attachment_file(attachment['digest']),
                                    attachment['content_type'])
            media_ids.append(media_id)
    except TwythonError as e:
        abort(400, str(e))
    if not len(media_ids):
        media_ids = None
    # Create the twitter status and grab the permalink
    try:
        url = create_tweet(tw, data['content']['text'], media_ids=media_ids)
    except TwythonError as e:
        abort(400, str(e))
    # Append the syndication link and `PATCH` the original post
    links.append({'entity': TWITTER_ENTITY, 'type': 'syndication', 'url': url})
    return (post_id, links)


def create_tweet(tw, status, media_ids=None):
    '''
    Create a Twitter API post.

    :param tw: the Twitter object to use to send the request.
    :param status: the text of the Twitter post.
    :param media: optional paths to media objects as attachments.
    :returns: permalink to the status post.
    '''
    post = tw.update_status(status=status, media_ids=media_ids)
    url = os.path.join(TWITTER_ENTITY, post['user']['screen_name'],
                       'status', post['id_str'])
    return url


def upload_media(tw, media_path, media_type):
    '''
    Uploads a media file to Twitter in order to attach it to a status.

    :param tw: the Twitter object to use to send the request.
    :param media: the media to be attached.
    :returns: media_id returned from Twitter.
    '''
    with open(media_path, 'rb') as media:
        post = tw.upload_media(media=media, image_type=media_type)
    return post['media_id']
