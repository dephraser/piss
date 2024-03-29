# -*- coding: utf-8 -*-

# This turns off the links feature to save some bandwidth / processing. Comment
# this out if you'd like to navigate the API via a browser
HATEOAS = True

# ENDPOINT DEFINITIONS
posts = {
    # 'title' tag used in item links. Defaults to the resource title minus
    # the final, plural 's' (works fine in most cases but not for 'people')
    'item_title': 'post',
    
    # This resource item endpoint will match a NewBase60 regex
    'item_url': 'regex("[0-9A-HJ-NP-Z_a-km-z]{5,9}")',
    
    # Sort in reverse chronological order
    'datasource': {
        'default_sort': [('_created', -1)]
    },

    # We choose to override global cache-control directives for this resource.
    'cache_control': 'max-age=10,must-revalidate',
    'cache_expires': 10,
    
    # Always return the type of the post after a successful `POST`
    'extra_response_fields': ['type'],
    
    'schema': {
        # Entity that published the post. This will be an ID that refers to an
        # entities endpoint
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
                },
                # JSON Patch of the tokenized (by whitespace) string
                'delta': {
                    'type': 'dict'
                }
            }
        },
        # Link or ID of the subscription that generated the post
        'source': {
            'type': 'string'
        },
        # The entities and posts that this post is referencing
        'links': {
            'type': 'list',
            'schema': {
                'type': 'dict',
                'schema': {
                    # Refers to the ID of the entity
                    'entity': {
                        'type': 'string'
                    },
                    'url': {
                        'type': 'string'
                    },
                    # Refers to the ID of the post if it's stored internally
                    'post': {
                        'type': 'string'
                    },
                    'version': {
                        'type': 'string'
                    },
                    # Name of the `content` key in OPP
                    'field': {
                        'type': 'string'
                    },
                    'sub_string': {
                        'type': 'string'
                    },
                    # The type of the post you're linking to. If the link is
                    # external, this should be parsed from the context somehow
                    # or simply set to 'external'
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
                    # attachment. This is used as an ID against the attachment
                    # endpoint.
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
                # Entities ost identifier of the application
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
                            # Post identifier of the group. Group posts will 
                            # have an entities post type
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

# Everything is a post. It will be up to apps to determine what post types to 
# query for and how to display them.
DOMAIN = {
    'posts': posts
}

# Enable document version control
VERSIONING = True

# API OPERATIONS
# Enable reads (GET), inserts (POST) and DELETE for resources/collections
# (if you omit this line, the API will default to ['GET'] and provide
# read-only access to the endpoint).
RESOURCE_METHODS = ['GET', 'POST']

# Enable reads (GET), edits (PATCH), replacements (PUT) and deletes of
# individual items  (defaults to read-only item access).
ITEM_METHODS = ['GET', 'PATCH', 'PUT', 'DELETE']

# Grant public access to only the GET methods
PUBLIC_METHODS = []
PUBLIC_ITEM_METHODS = []

# DATABASE SETTINGS
MONGO_DBNAME = 'piss'
