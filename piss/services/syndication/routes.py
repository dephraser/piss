# -*- coding: utf-8 -*-

'''
Syndication Routes
'''

from flask import abort, Blueprint, current_app, request
from eve.methods.patch import patch_internal
from piss.auth import requires_auth
from piss.services.utils import render_response
from .twitter import twitter_handler
from .fb import facebook_handler

VALID_SERVICES = ('twitter','facebook')
syndication = Blueprint('syndication', __name__)


@syndication.route('/syndicate/<service>', methods=['POST'])
@requires_auth()
def syndicate(service):
    '''
    Syndicate a post to the given service. Checks if the original post exists
    and if it hasn't been syndicated to the given service already.

    :param service: the service to syndicate to.
    '''
    service = service.lower()
    if service not in VALID_SERVICES:
        abort(400, 'Service not recognized.')

    if request.mimetype != 'application/json':
        abort(400, 'Syndication endpoint only accepts JSON data.')

    # Get the data and launch the handler for the appropriate service
    data = request.json
    meta_post = current_app.config.get('META_POST')
    post_id, links = eval('%s_handler' % service)(data, meta_post['entity'])
    
    # Patch the original post with the new links object
    response, _, _, status = patch_internal('posts', {'links': links},
                                            concurrency_check=False,
                                            **{'_id': post_id})
    if status not in (200, 201):
        abort(status)
    return render_response(response, 'item.html',
                           title="Syndicate to %s"
                           % (service.lower().capitalize(),))
