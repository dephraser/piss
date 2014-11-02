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
from piss.utils import get_post_by_id
from .utils import is_duplicate_syndication, validate_service

TWITTER_ENTITY = 'https://twitter.com/'


def twitter_handler(data, server_entity):
    '''
    Syndicates request data to Twitter.

    :param data: request data with syndication information.
    :param server_entity: the entity we are syndicating for.
    '''
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
    # Create the twitter status and grab the permalink
    try:
        url = create_tweet(data['content']['text'])
    except TwythonError as e:
        abort(400, str(e))
    # Append the syndication link and `PATCH` the original post
    links.append({'entity': TWITTER_ENTITY, 'type': 'syndication', 'url': url})
    return (post_id, links)


def create_tweet(status):
    '''
    Create a Twitter API post.

    :param status: the text of the Twitter post.
    :returns: permalink to the status post.
    '''
    # Get the Twitter configuration
    tw_conf = current_app.config.get('TWITTER', None)
    if not tw_conf:
        abort(400, 'Twitter not configured on the server.')
    twitter = Twython(tw_conf['app_key'], tw_conf['app_secret'],
                      tw_conf['token'], tw_conf['token_secret'])
    post = twitter.update_status(status=status)
    url = os.path.join(TWITTER_ENTITY, post['user']['screen_name'], 'status',
                       post['id_str'])
    return url

