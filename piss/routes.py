# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, current_app, make_response, render_template, send_from_directory, abort
from eve.render import render_xml
from .html_renderer.decorators import request_is_json, request_is_xml
from .attachments import get_attachment_dir

server = Blueprint('server', __name__)

@server.route('/meta')
def meta():
    '''
    Return the `meta` post for the server. Checks the `Accept` header to 
    return a response of the appropriate type.
    '''
    if request_is_json():
        return jsonify(current_app.config['META_POST'])
    elif request_is_xml():
        response = make_response(render_xml(current_app.config['META_POST']))
        response.mimetype = 'application/xml'
        response.charset = 'utf-8'
        return response
    else:
        return render_template('meta.html', item=current_app.config['META_POST'])

@server.route('/attachments/<digest>')
def attachments(digest):
    '''
    Given an attachment digest, find a post that lists the digest in its 
    `attachments` array and return the relevant file.
    '''
    posts = current_app.data.driver.db['posts']
    lookup = {
        'attachments': {
            '$elemMatch': {
                'digest': digest
            }
        }
    }
    attachment_post = posts.find_one(lookup)
    if not attachment_post:
        abort(404)
    for attachment in attachment_post['attachments']:
        if attachment['digest'] == digest:
            break
    else:
        # We never found a matching digest -- abort
        abort(404)
    return send_from_directory(get_attachment_dir(digest), digest, mimetype=attachment['content_type'])

@server.route('/posts/<pid>/<name>')
def post_attachment(pid, name):
    '''
    Given a post ID and file name, retrieve the post, find the matching 
    attachment, and return the relevant file.
    '''
    posts = current_app.data.driver.db['posts']
    attachment_post = posts.find_one({'_id': pid})
    if not attachment_post:
        abort(404)
    for attachment in attachment_post['attachments']:
        if attachment['name'] == name:
            break
    else:
        # We never found a matching name -- abort
        abort(404)
    digest = attachment['digest']
    return send_from_directory(get_attachment_dir(digest), digest, mimetype=attachment['content_type'])
