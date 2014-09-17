import os
import time
import hashlib
from eve import Eve
from eve.io.mongo import MongoJSONEncoder
from eve.io.mongo import Validator

settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')

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
        print isinstance(obj, NewBase60)
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
    current_time = int(time.time())
    for document in documents:
        # Create version information
        if not 'version' in document.keys():
            digest = create_version_digest(document)
            document['version'] = create_version_document(digest, current_time)
        
        # Create an ID for the document
        document['_id'] = str(NewBase60(current_time))

def before_update(resource, updates, original):
    current_time = int(time.time())
    # Create an updated version of the original *without* the `version` field
    updated = original.copy()
    updated.update(updates)
    try:
        del(updated['version'])
    except KeyError as e:
        # Weird that it didn't have it, but just as well
        pass
    
    # Create version information and append it to the updates
    digest = create_version_digest(updated)
    updates['version'] = create_version_document(digest, current_time)

def create_version_digest(document):
    hasher = hashlib.sha512()
    hasher.update(str(document))
    # Hex-encoded first 256 bits of the SHA-512
    return hex(int(hasher.hexdigest(), 16) >> 256)

def create_version_document(digest, current_time):
    version_document = {}
    version_document['id'] = digest
    version_document['published_at'] = current_time * 1000
    return version_document

app = Eve(settings=settings_file, 
          json_encoder=NewBase60Encoder, 
          validator=NewBase60Validator)
app.on_insert += before_insert
app.on_update += before_update

if __name__ == '__main__':
    app.run()
