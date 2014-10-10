# -*- coding: utf-8 -*-

from eve.auth import HMACAuth
from flask import current_app, request, g
import hawk
from hawk.util import HawkException
from .utils import get_post_by_id, is_collection_path

def get_credentials_from_post_id(cid):
    '''
    Retrieve the credentials post for the given ID and convert it to
    a format suitable for Hawk authentication. If the ID is given as `root`, the
    server will check against the credentials given in `ROOT_CREDENTIALS` in 
    `piss.cfg`.
    '''
    if cid == 'root':
        return current_app.config.get('ROOT_CREDENTIALS')
    
    cred_post = get_post_by_id(cid)
    if not cred_post:
        return False
    if cred_post.get('content', None) is None:
        return False
    if cred_post['content'].get('hawk_algorithm', None) is None or cred_post['content'].get('hawk_key', None) is None:
        return False
    return {
        'id': str(cid),
        'algorithm': str(cred_post['content']['hawk_algorithm']),
        'key': str(cred_post['content']['hawk_key'])
    }

class HawkAuth(HMACAuth):
    def check_auth(self, http_auth, host, port, path, query_string, allowed_roles, method):
        req = {
            'method': method,
            'url': '%s?%s' % (path, query_string,),
            'host': host,
            'port': port,
            'headers': {
                'authorization': http_auth
            }
        }
        server = hawk.Server(req, get_credentials_from_post_id)
        options = {}
        
        try:
            if 'bewit=' in query_string:
                # Never accept bewits for collections. Just say no.
                if is_collection_path(path):
                    return False
                if server.authenticate_bewit(options):
                    return True
            else:
                if server.authenticate(options):
                    return True
        except KeyError:
            return False
        except HawkException:
            return False
        except Exception:
            # TODO: Rather than return `False`, `get_credentials_from_post_id`
            # should raise a custom exception when it can't find a credentials
            # post
            return False
        
        # We really should have returned already... Default to False
        return False

    def authorized(self, allowed_roles, resource, method):
        http_auth = request.headers.get('Authorization', '')
        
        bewit_query = request.args.get('bewit', '')
        path = request.environ['PATH_INFO']
        if http_auth or bewit_query:
            query_string = request.environ.get('QUERY_STRING', '')
            host = request.environ['HTTP_HOST']
            port = ''
            if ':' in host:
                host, port = request.environ['HTTP_HOST'].split(':')
            
            return self.check_auth(http_auth, host, port, path, query_string,
                                        allowed_roles, method)
        else:
            # Return True for `GET` requests but set a flag so that event
            # hooks are wary and can filter the request appropriately.
            if method == 'GET':
                g.non_authed_GET = True
                return True
            return False
