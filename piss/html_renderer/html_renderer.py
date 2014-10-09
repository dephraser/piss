# -*- coding: utf-8 -*-

import os
import json
import jinja2
from flask import Flask, request, render_template, abort, jsonify, url_for, make_response
from eve.methods import get, getitem
from .decorators import html_renderer_for


def HTML_Renderer(app):
    # Set directory for HTML templates
    templates_path = os.path.join(os.path.dirname(app.instance_path), 'templates')
    app.jinja_loader = jinja2.FileSystemLoader(templates_path)
    
    # Set directory for static files
    app.static_folder = os.path.join(os.path.dirname(app.instance_path), 'static')
    
    # Routes
    @html_renderer_for('home')
    def home_wrapper():
        response = make_response(render_template('home.html'))
        meta_post_link = str(url_for('server.meta', _external=True)) + '; rel="meta-post"'
        response.headers.add('Link', meta_post_link)
        return response

    @html_renderer_for('resource')
    def resource_wrapper(resource, method, **lookup):
        response = None
        if method in ('GET', 'HEAD'):
            response, last_modified, etag, status = get(resource, lookup)
        elif method == 'OPTIONS':
            return app.make_default_options_response()
        else:
            abort(401)
        links = response.pop('_links', {})
        items = response.pop('_items', [])
        return render_template('items.html', obj=items, links=links)

    @html_renderer_for('item')
    def item_lookup_wrapper(resource, method, **lookup):
        response = None
        if method in ('GET', 'HEAD'):
            response, last_modified, etag, status = getitem(resource, lookup)
        elif method == 'OPTIONS':
            return app.make_default_options_response()
        else:
            abort(401)
        links = response.pop('_links', {})
        return render_template('item.html', obj=response, links=links)

    @html_renderer_for('error')
    def error_wrapper(error):
        return render_template('error.html', code=error.code, message=error.description), error.code
    
    # Override Eve's view functions with our own.
    for key in app.view_functions:
        # Split the key at the pipe and get the last item
        func_name = key.split('|')[-1]
        
        if func_name == 'home':
            app.view_functions[key] = home_wrapper
        elif func_name == 'resource':
            app.view_functions[key] = resource_wrapper
        elif func_name == 'item_lookup' or func_name == 'item_additional_lookup':
            app.view_functions[key] = item_lookup_wrapper
    
    # Override Eve's error handler functions
    for code in app.error_handler_spec[None]:
        app.error_handler_spec[None][code] = error_wrapper
    
    # Create custom Jinja filters
    @app.template_filter('ppjson')
    def json_pretty_print(dictionary):
        if dictionary is None or type(dictionary) is not dict:
            return dictionary
        return json.dumps(dictionary, sort_keys=True, indent=4, separators=(',', ': '))
    
    @app.template_filter('basename')
    def get_basename_from_path(path):
        '''
        Get the last node in a path or URL. Strips all slashes from the end
        of a path before attempting to get the basename.
        '''
        new_path = path
        while len(new_path):
            if new_path[-1] == '/' or new_path[-1] == '\\':
                new_path = new_path[:-1]
            else:
                break
        basename = os.path.basename(new_path)
        if basename:
            return basename
        else:
            return path
    
    # Jinja test for lists
    def is_list(value):
        return isinstance(value, list)
    app.jinja_env.tests['list'] = is_list
    
    # Set some additional headers for non-XML and non-JSON requests
    @app.after_request
    def process_response(response):
        if request.method == 'GET': 
            for mimetype in ('application/json', 'application/xml'):
                if not mimetype in response.mimetype:
                    response.headers['X-UA-Compatible'] = 'IE=edge'
                    response.headers['Content-Security-Policy'] = "default-src 'self'; font-src 'self' https://themes.googleusercontent.com; frame-src 'none'; object-src 'none'"
                    break
        return response
