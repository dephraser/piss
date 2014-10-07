# -*- coding: utf-8 -*-

import functools
from flask import request
from eve.endpoints import collections_endpoint, item_endpoint, home_endpoint, error_endpoint
from eve.utils import request_method

# Outer decorator allows me to supply an argument
def html_renderer_for(request_type):
    # Set the appropriate Eve function to return based on the request type
    if request_type == 'home':
        eve_view_func = home_endpoint
    elif request_type == 'resource':
        eve_view_func = collections_endpoint
    elif request_type == 'item':
        eve_view_func = item_endpoint
    elif request_type == 'error':
        eve_view_func = error_endpoint
    
    # The 'real' decorator that will determine whether a request should be
    # dispatched by the wrapper or by the Eve view function
    def dispatch_request_by_type(wrapper_func):
        @functools.wraps(wrapper_func)
        def wrapper(*args, **kwargs):
            # If the request is XML or JSON, return the Eve endpoint
            if request_is_xml() or request_is_json():
                return eve_view_func(*args, **kwargs)
            
            # If the request is for the `item` or `resource` endpoints, get
            # the resource name and method and feed them to the HTML renderer
            if request_type == 'item' or request_type == 'resource':
                resource = _resource()
                method = request_method()
                return wrapper_func(resource, method, **kwargs)
            
            # For all other endpoints, return the HTML renderer
            return wrapper_func(*args, **kwargs)
        
        return wrapper
    return dispatch_request_by_type

# Websites serve content from a variety of different mime-types, i.e. 
# images, css files, etc. Rather than check for every possible file type,
# check only for XML and JSON so that Eve can handle them, and assume
# everything else is sent to the HTML renderer.
def request_is_xml():
    best = request.accept_mimetypes \
        .best_match(['application/xml', 'text/html'])
    return best == 'application/xml' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

def request_is_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

def _resource():
    return request.endpoint.split('|')[0]