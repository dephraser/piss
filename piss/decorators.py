# -*- coding: utf-8 -*-

import functools
from eve.endpoints import collections_endpoint, item_endpoint, home_endpoint, error_endpoint
from eve.utils import request_method
from piss.utils import request_is_xml, request_is_json, _resource

# Outer decorator allows me to supply an argument
def html_renderer_for(request_type):
    # Dict of appropriate Eve function to return based on the request type
    eve_view_func = {
        'home': home_endpoint,
        'resource': collections_endpoint,
        'item': item_endpoint,
        'error': error_endpoint
    }
    
    # The 'real' decorator that will determine whether a request should be
    # dispatched by the wrapper or by the Eve view function
    def dispatch_request_by_type(wrapper_func):
        @functools.wraps(wrapper_func)
        def wrapper(*args, **kwargs):
            # If the request is XML or JSON, return the Eve endpoint
            if request_is_xml() or request_is_json():
                return eve_view_func[request_type](*args, **kwargs)
            
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
