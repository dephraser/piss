# -*- coding: utf-8 -*-

'''
Attachments routes

Routes use Eve's `getitem` to fetch attachment data, so authorization is
handled automatically.
'''

from flask import abort, Blueprint, request, send_from_directory
from eve.methods import getitem
from piss.file_io import get_attachment_dir

attachments = Blueprint('attachments', __name__)


@attachments.route('/attachments/<digest>')
def attachment(digest):
    '''
    Given an attachment digest, find a post that lists the digest in its
    `attachments` array and return the relevant file.

    :param digest: the attachment digest.
    '''
    lookup = {
        'attachments': {
            '$elemMatch': {
                'digest': digest
            }
        }
    }
    attachment = get_attachment('digest', digest, lookup)
    return send_from_directory(get_attachment_dir(digest), digest,
                               mimetype=attachment['content_type'])


@attachments.route('/posts/<pid>/<name>')
def post_attachment(pid, name):
    '''
    Given a post ID and file name, retrieve the post, find the matching
    attachment, and return the relevant file.

    :param pid: the post ID.
    :param name: the attachment name.
    '''
    attachment = get_attachment('name', name, {'_id': pid})
    digest = attachment['digest']
    return send_from_directory(get_attachment_dir(digest), digest,
                               mimetype=attachment['content_type'])


def get_attachment(key, value, lookup):
    '''
    Performs a lookup for a particular post and returns an attachment document
    if one of its keys matches the given value. Also makes sure to reject
    `version` requests that would be impossible to fulfill.

    :param key: the dict key to match.
    :param value: the dict value at the given key to match.
    :param lookup: dict used to filter results in a database lookup.
    '''
    if 'version' in request.args \
            and request.args['version'] in ('all', 'diffs'):
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
