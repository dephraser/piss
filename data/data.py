import os
import time
import hashlib
from eve import Eve

settings_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'settings.py')

def before_insert(resource, documents):
    for document in documents:
        hasher = hashlib.sha512()
        hasher.update(str(document))
        # Hex-encoded first 256 bits of the SHA-512
        digest = hex(int(hasher.hexdigest(), 16) >> 256)
        if not 'version' in document.keys():
            document['version'] = {}
        document['version']['id'] = digest
        if not 'published_at' in document['version'].keys():
            document['version']['published_at'] = int(time.time() * 1000)

app = Eve(settings=settings_file)
app.on_insert += before_insert

if __name__ == '__main__':
    app.run()
