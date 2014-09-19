import os
import functools
from flask import Flask, render_template, request
from eve.endpoints import collections_endpoint, item_endpoint, home_endpoint
from eve.utils import parse_request
import jinja2

# The static folder can only be set on init, so it's here so Eve can import
HTML_STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

def HTML_Renderer(app):
    # Set directory for HTML templates
    templates_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
    app.jinja_loader = jinja2.FileSystemLoader(templates_path)
    
    # Outer decorator allows me to supply an argument
    def html_renderer_for(eve_view_func):
        # The 'real' decorator that will determine whether a request should be
        # dispatched by the wrapper or by the Eve view function
        def dispatch_request_by_type(wrapper_func):
            @functools.wraps(wrapper_func)
            def wrapper(*args, **kwargs):
                if request_is_xml() or request_is_json():
                    return eve_view_func(*args, **kwargs)
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

    @html_renderer_for(home_endpoint)
    def home_wrapper():
        return render_template('index.html')

    @html_renderer_for(collections_endpoint)
    def posts_resource_wrapper(**lookup):
        resource = 'posts'
        req = parse_request(resource)
        posts = app.data.find(resource, req, lookup)
        return str(list(posts))

    @html_renderer_for(item_endpoint)
    def posts_item_lookup_wrapper(**lookup):
        resource = 'posts'
        req = parse_request(resource)
        post = app.data.find_one(resource, req, **lookup)
        return str(post)

    @html_renderer_for(item_endpoint)
    def types_item_additional_lookup_wrapper(**lookup):
        resource = 'types'
        req = parse_request(resource)
        post_type = app.data.find_one(resource, req, **lookup)
        return str(post_type)

    # You can view which view function identifiers you have available to override
    # by looking at the rules in `app.url_map`
    app.view_functions['home'] = home_wrapper
    app.view_functions['posts|resource'] = posts_resource_wrapper
    app.view_functions['posts|item_lookup'] = posts_item_lookup_wrapper
    app.view_functions['types|item_additional_lookup'] = types_item_additional_lookup_wrapper
    
    @app.after_request
    def process_response(response):
        # TODO: Only add these headers if the response's content-type is text/html
        if not 'application/json' in response.mimetype and not 'application/xml' == response.mimetype:
            response.headers['X-UA-Compatible'] = 'IE=edge'
            response.headers['Content-Security-Policy'] = "default-src 'self'; font-src 'self' https://themes.googleusercontent.com; frame-src 'none'; object-src 'none'"
        return response