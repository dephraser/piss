# GENERAL CONFIGURATION
#API_VERSION = '0.1'
#ID_FIELD = 'id'

# Custom date format
# DATE_FORMAT = '%d %b %Y %H:%M:%S'

# This turns off the links feature to save some bandwidth / processing. Comment
# this out if you'd like to navigate the API via a browser
HATEOAS = True

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
        # Entity that published the post
        'entity': {
            'type': 'string',
            'required': True,
        },
        # Publishing time at the app level. Number of milliseconds since the
        # UNIX epoch. If there are issues with the network this may be
        # different from Eve's `created` date
        'published_at': {
            'type': 'integer'
        },
        # The server automatically creates a `version` object that includes
        # an `id`, which is the hex-encoded first 256 bits of the SHA-512 of
        # the contents of the post, and the `published_at` date. However, an
        # app may include a version field itself if it's specifically
        # creating a new version of an existing post.
        'version': {
            'type': 'dict',
            'schema': {
                'published_at': {
                    'type': 'integer'
                },
                'parents': {
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'version': {
                                'type': 'string',
                                'required': True
                            },
                            'entity': {
                                'type': 'string'
                            },
                            'post': {
                                'type': 'string'
                            }
                        }
                    }
                },
                'message': {
                    'type': 'string'
                }
            }
        },
        # The entities and posts that this post is referencing
        'links': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'entity': {
                        'type': 'string'
                    },
                    'post': {
                        'type': 'string'
                    },
                    'version': {
                        'type': 'string'
                    },
                    'field': {
                        'type': 'string'
                    },
                    'sub_string': {
                        'type': 'dict',
                        'schema': {
                            'start': {
                                'type': 'integer'
                            },
                            'end': {
                                'type': 'integer'
                            }
                        }
                    },
                    'type': {
                        'type': 'string'
                    }
                }
            }
        },
        # Licenses that the post is released under
        'licenses': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    'name': {
                        'type': 'string'
                    },
                    'url': {
                        'type': 'string'
                    }
                }
            }
        },
        # The post type URI
        'type': {
            'type': 'string',
            'required': True
        },
        # The actual content of a post
        'content': {
            'type': 'dict'
        },
        # Documents attached to the post. Generally used to reference binary
        # data
        'attachments': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    # This should be the same format as `Content-Type` in HTTP
                    'content_type': {
                        'type': 'string'
                    },
                    'name': {
                        'type': 'string'
                    },
                    # The hex-encoded first 256 bits of the SHA-512 of the 
                    # attachment
                    'digest': {
                        'type': 'string'
                    },
                    'size': {
                        'type': 'integer'
                    }
                }
            }
        },
        # Application that published the post
        'app': {
            'type': 'dict',
            'schema': {
                # Post identifier of the application
                'post': {
                    'type': 'string'
                },
                'name': {
                    'type': 'string'
                },
                'url': {
                    'type': 'string'
                }
            }
        },
        # This object should be omitted if `public` is True
        'permissions': {
            'type': 'dict',
            'schema': {
                'public': {
                    'type': 'boolean'
                },
                # List of groups that are permitted access
                'groups': {
                    'type': 'list',
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'name': {
                                'type': 'string'
                            },
                            # Post identifier of the group
                            'post': {
                                'type': 'string',
                                'required': True
                            }
                        }
                    }
                },
                # List of entities that are permitted to access
                'entities': {
                    'type': 'list',
                    'schema': {
                        'type': 'string'
                    }
                }
            }
        }
    }
}

DOMAIN = {
    'posts': posts,
    'opp': posts
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
