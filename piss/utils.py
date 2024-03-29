# -*- coding: utf-8 -*-

from flask import current_app, request
from eve.io.mongo import MongoJSONEncoder
from eve.io.mongo import Validator

class NewBase60(object):
    '''
    An object that can accept an integer and save it internally as a NewBase60
    string, or vice versa. Type-casting a NewBase60 object to an `int` or a
    `str` will return the appropriate result.
    '''
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

def get_post_by_id(post_id):
    '''
    Retrieve a post for the given ID.
    '''
    posts = current_app.data.driver.db['posts']
    lookup = {'_id': post_id}
    post = posts.find_one(lookup)
    if post is None or type(post) is not dict:
        return False
    else:
        return post

def is_collection_request(request):
    '''
    Determines if the specified request points to a resource collection.
    '''
    path = request.environ['PATH_INFO']
    return is_collection_path(path)

def is_collection_path(path):
    '''
    Determines if the specified request points to a resource collection.
    '''
    # Strip start and end slashes and split by any slashes that remain
    path_split = path.rstrip('/').lstrip('/').split('/')
    if len(path_split) == 1 and path_split[0] in current_app.config['DOMAIN']:
        return True
    return False

def request_is_xml():
    '''
    Analyze the request object and determine if the headers indicate XML.
    '''
    best = request.accept_mimetypes \
        .best_match(['application/xml', 'text/html'])
    return best == 'application/xml' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

def request_is_json():
    '''
    Analyze the request object and determine if the headers indicate JSON.
    '''
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

def _resource():
    '''
    Internally, endpoints use the pipe character to separate the resource name
    from its handler function.
    '''
    return request.endpoint.split('|')[0]
