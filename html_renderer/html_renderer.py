import os
import jinja2
from flask import Flask, request, render_template, abort
from eve.methods import get, getitem
from .decorators import html_renderer_for


# The static folder can only be set on init, so it's here so Eve can import
HTML_STATIC_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

def HTML_Renderer(app):
    # Set directory for HTML templates
    templates_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
    app.jinja_loader = jinja2.FileSystemLoader(templates_path)
    
    # Routes
    @html_renderer_for('home')
    def home_wrapper():
        return render_template('index.html')

    @html_renderer_for('resource')
    def posts_resource_wrapper(resource, method, **lookup):
        response = None
        if method in ('GET', 'HEAD'):
            response, last_modified, etag, status = get(resource, lookup)
        else:
            abort(401)
        return str(response)

    @html_renderer_for('item')
    def posts_item_lookup_wrapper(resource, method, **lookup):
        response = None
        if method in ('GET', 'HEAD'):
            response, last_modified, etag, status = getitem(resource, lookup)
        else:
            abort(401)
        return str(response)

    @html_renderer_for('resource')
    def types_resource_wrapper(resource, method, **lookup):
        response = None
        if method in ('GET', 'HEAD'):
            response, last_modified, etag, status = get(resource, lookup)
        else:
            abort(401)
        return str(response)

    @html_renderer_for('item')
    def types_item_lookup_wrapper(resource, method, **lookup):
        response = None
        if method in ('GET', 'HEAD'):
            response, last_modified, etag, status = getitem(resource, lookup)
        else:
            abort(401)
        return str(response)

    @html_renderer_for('error')
    def error_wrapper(error):
        return render_template('error.html', code=error.code, message=error.description), error.code
    
    # Override Eve's view functions with our own. You can view which view
    # function identifiers you have available to override by looking at the
    # rules in `app.url_map`
    app.view_functions['home'] = home_wrapper
    app.view_functions['posts|resource'] = posts_resource_wrapper
    app.view_functions['posts|item_lookup'] = posts_item_lookup_wrapper
    app.view_functions['types|resource'] = types_resource_wrapper
    app.view_functions['types|item_lookup'] = types_item_lookup_wrapper
    app.view_functions['types|item_additional_lookup'] = types_item_lookup_wrapper
    
    # Override Eve's error handler functions
    for code in [400, 401, 403, 404, 422]:
        app.error_handler_spec[None][code] = error_wrapper
    
    # Set some additional headers for non-XML and non-JSON requests
    @app.after_request
    def process_response(response):
        if request.method == 'GET' and not 'application/json' in response.mimetype and not 'application/xml' in response.mimetype:
            response.headers['X-UA-Compatible'] = 'IE=edge'
            response.headers['Content-Security-Policy'] = "default-src 'self'; font-src 'self' https://themes.googleusercontent.com; frame-src 'none'; object-src 'none'"
        return response
