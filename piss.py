import os
import time
import hashlib
from eve import Eve
from eve.io.mongo import MongoJSONEncoder
from eve.io.mongo import Validator
from eve.auth import HMACAuth
from eve.methods.post import post_internal
from flask import request
import hawk
from hawk.util import HawkException
from hawk.hcrypto import random_string
from html_renderer import HTML_Renderer, HTML_STATIC_FOLDER

class NewBase60(object):
    def __init__(self, integer=None, string=None):
        self._integer = integer
        self._string = string
        self._NB60AB = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ_abcdefghijkmnopqrstuvwxyz'
        
        if not self._integer == None and (type(self._integer) is int or type(self._integer) is long):
            self._string = self.__get_str()
        elif not self._string == None and type(self._string) is str:
            self._integer = self.__get_int()
        else:
            raise ValueError('Arguments must be positive integers or strings in the NewBase60 alphabet')
    
    def __str__(self):
        return self._string
    
    def __int__(self):
        return self._integer
    
    def __digits(self, n, base):
        if not isinstance(n, (int, long)):
            raise ValueError('Arg n must be an int or long, got {}'.format(type(n)))
        if n < 0:
            raise ValueError('Arg n must not be less than 0.')
        if not isinstance(base, (int, long)):
            raise ValueError('Arg base must be an int or long, got {}'.format(type(base)))
        if base < 2:
            raise ValueError('Base must be greater than 2.')
        if n == 0:
            return [0]
        l = []
        while n > 0:
            n, r = divmod(n, base)
            l.append(r)
        return l[::-1]
    
    def __get_int(self):
        if not set(self._string).issubset(set(self._NB60AB)):
            raise ValueError('String contains characters not present in NewBase60 alphabet')
        n = 0
        base = len(self._NB60AB)
        for i, v in enumerate(self._string[::-1]):
            n += self._NB60AB.index(v) * (base**i)
        return n
    
    def __get_str(self):
        d = self.__digits(self._integer, len(self._NB60AB))
        str_ab = [str(x) for x in self._NB60AB]
        return ''.join([str_ab[x] for x in d])

class NewBase60Encoder(MongoJSONEncoder):
    """ JSONEconder subclass used by the json render function.
    This is different from BaseJSONEoncoder since it also addresses
    encoding of NewBase60
    """
    def default(self, obj):
        if isinstance(obj, NewBase60):
            return str(obj)
        else:
            # delegate rendering to base class method (the base class
            # will properly render ObjectIds, datetimes, etc.)
            return super(NewBase60Encoder, self).default(obj)

class NewBase60Validator(Validator):
    """
    Extends the base mongo validator adding support for NewBase60
    """
    def _validate_type_newbase60(self, field, value):
        try:
            NewBase60(value)
        except ValueError:
            self._error(field, "value '%s' cannot be converted to NewBase60" %
                        value)

def before_insert(resource, documents):
    meta_post = app.config.get('META_POST')
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

def before_update(resource, updates, original):
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

def pre_posts_get_callback(request, lookup):
    '''
    Before performing a GET request, check the authorization headers. If no
    auth headers are found or the auth is an incorrect type, set the lookup to
    find only public posts.
    '''
    http_auth = request.headers.get('Authorization')
    bewit_query = request.args.get('bewit')
    if not http_auth and not bewit_query:
        lookup['permissions'] = {'public': True}

def get_credentials_from_post_id(cid):
    '''
    Retrieve the credentials post for the given ID and convert it to
    a format suitable for Hawk authentication. If the ID is given as `root`, the
    server will check against the credentials given in `ROOT_CREDENTIALS` in 
    `piss.cfg`.
    '''
    if cid == 'root':
        return app.config.get('ROOT_CREDENTIALS')
    
    posts = app.data.driver.db['posts']
    lookup = {'_id': cid}
    cred_post = posts.find_one(lookup)
    if cred_post is None:
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

# Grab the paths for the Eve settings file and the instance folder
settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')
instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')

app = Eve(settings=settings_file, 
          json_encoder=NewBase60Encoder, 
          validator=NewBase60Validator,
          auth=HawkAuth,
          instance_path=instance_path,
          static_folder=HTML_STATIC_FOLDER)

app.on_insert += before_insert
app.on_update += before_update
app.on_pre_GET_posts += pre_posts_get_callback

# Load some instance configuration settings
app.config.from_pyfile(os.path.join(instance_path, 'piss.cfg'), silent=True)

HTML_Renderer(app)

if __name__ == '__main__':
    app.run()
