# GENERAL CONFIGURATION
API_VERSION = '0.1'
#ID_FIELD = 'id'

# Custom date format
DATE_FORMAT = '%d %b %Y %H:%M:%S GMT'

# This turns off the links feature to save some bandwidth / processing. Comment
# this out if you'd like to navigate the API via a browser
HATEOAS = False

# If you want to use the server as a standalone without breaking your client
# app functionality, uncomment the line below
#URL_PREFIX = 'api'

# ENDPOINT DEFINITIONS
posts = {
    # 'title' tag used in item links. Defaults to the resource title minus
    # the final, plural 's' (works fine in most cases but not for 'people')
    'item_title': 'post',

    # We choose to override global cache-control directives for this resource.
    'cache_control': 'max-age=10,must-revalidate',
    'cache_expires': 10,

    # most global settings can be overridden at resource level. We're disabling
    # DELETE here.
    'resource_methods': ['GET', 'POST'],

    'schema': {
        # Schema definition, based on Cerberus grammar. Check the Cerberus project
        # (https://github.com/nicolaiarocci/cerberus) for details.
        'title': {
            'type': 'string',
            'minlength': 3,
            'maxlength': 256,
            'required': True,
        }
    }
}

DOMAIN = {
    'posts': posts,
}

# API OPERATIONS
# Enable reads (GET), inserts (POST) and DELETE for resources/collections
# (if you omit this line, the API will default to ['GET'] and provide
# read-only access to the endpoint).
RESOURCE_METHODS = ['GET', 'POST', 'DELETE']

# Enable reads (GET), edits (PATCH), replacements (PUT) and deletes of
# individual items  (defaults to read-only item access).
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']

# DATABASE SETTINGS
# Let's just use the local mongod instance. Edit as needed.

# Please note that MONGO_HOST and MONGO_PORT could very well be left
# out as they already default to a bare bones local 'mongod' instance.
MONGO_HOST = 'localhost'
MONGO_PORT = 27017

# If you don't create a database and associated users, Eve will simply create
# an `eve` database in Mongo
#MONGO_USERNAME = 'user'
#MONGO_PASSWORD = 'user'
#MONGO_DBNAME = 'isisapp'