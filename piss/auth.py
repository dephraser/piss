from eve.auth import HMACAuth
from flask import current_app, request
import hawk
from hawk.util import HawkException
from .utils import get_post_by_id

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
    if cred_post.get('content') is None:
        return False
    if cred_post['content'].get('hawk_algorithm') is None or cred_post['content'].get('hawk_key') is None:
        return False
    return {
        'id': str(cid),
        'algorithm': str(cred_post['content']['hawk_algorithm']),
        'key': str(cred_post['content']['hawk_key'])
    }

class HawkAuth(HMACAuth):
    def check_auth(self, http_auth, host, port, url, data, allowed_roles, resource, method):
        req = {
            'method': method,
            'url': url,
            'host': host,
            'port': port,
            'headers': {
                'authorization': http_auth
            }
        }
        server = hawk.Server(req, get_credentials_from_post_id)
        options = {}
        
        try:
            if url.find('bewit=') == -1:
                artifacts = server.authenticate(options)
            else:
                return server.authenticate_bewit(options)
        except KeyError:
            return False
        except HawkException:
            return False
        except Exception:
            # TODO: Rather than return `False`, `get_credentials_from_post_id`
            # should raise a custom exception when it can't find a credentials
            # post
            return False
        
        return True

    def authorized(self, allowed_roles, resource, method):
        http_auth = request.headers.get('Authorization')
        if not http_auth:
            http_auth = ''
        
        bewit_query = request.args.get('bewit')
        
        if http_auth or bewit_query:
            url = request.environ['PATH_INFO']
            if request.environ['QUERY_STRING']:
                url += '?' + request.environ['QUERY_STRING']
            
            host = request.environ['HTTP_HOST']
            port = ''
            if ':' in host:
                host, port = request.environ['HTTP_HOST'].split(':')
            
            return self.check_auth(http_auth, host, port, url,
                                        request.get_data(), allowed_roles,
                                        resource, method)
        else:
            # Return true for `GET` requests. This will be picked up by
            # `pre_posts_get_callback` to set the lookup to only public posts
            if method == 'GET':
                return True
            return False
