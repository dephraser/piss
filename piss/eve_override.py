# -*- coding: utf-8 -*-

import os
import jinja2
from flask import Flask, request, render_template, abort, url_for, make_response, send_from_directory
from werkzeug.utils import secure_filename
from eve.methods import get, getitem
from eve.render import raise_event
from .decorators import html_renderer_for

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)


def eve_override(app):
    # Set directory for HTML templates
    templates_path = os.path.join(CURRENT_DIR, 'templates')
    app.jinja_loader = jinja2.FileSystemLoader(templates_path)
    
    # Routes
    @html_renderer_for('home')
    def home_wrapper():
        response = make_response(render_template('home.html'))
        meta_post_link = str(url_for('server_info.meta', _external=True)) + '; rel="meta-post"'
        response.headers.add('Link', meta_post_link)
        return response

    @html_renderer_for('resource')
    @raise_event
    def resource_wrapper(resource, method, **lookup):
        response = get_response_by_method(get, resource, method, **lookup)
        obj = response.pop('_items', [])
        links = response.pop('_links', {})
        return make_response(render_template('items.html', obj=obj, links=links))

    @html_renderer_for('item')
    @raise_event
    def item_lookup_wrapper(resource, method, **lookup):
        obj = get_response_by_method(getitem, resource, method, **lookup)
        links = obj.pop('_links', {})
        return make_response(render_template('item.html', obj=obj, links=links))

    @html_renderer_for('error')
    def error_wrapper(error):
        return make_response(render_template('error.html', code=error.code, message=error.description), error.code)
    
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
    
    # Theme override
    current_theme = app.config.get('THEME', 'default')
    if not current_theme == 'default':
        theme_templates = os.path.join(ROOT_DIR, 'themes', current_theme, 'templates')
        if os.path.isdir(theme_templates):
            theme_loader = jinja2.ChoiceLoader([
                jinja2.FileSystemLoader(theme_templates),
                app.jinja_loader
            ])
            app.jinja_loader = theme_loader

    @app.route('/static/<path:filename>')
    def static(filename):
        '''
        Override Flask's default `static` function in order to look for files
        in a theme's `static` folder. If the file isn't found (or no theme is
        set), fetch the file from the default `static` folder.

        :param filename: the name of the file to fetch.
        '''
        path, filename = os.path.split(filename)
        filename = secure_filename(filename)
        current_theme = app.config.get('THEME', 'default')
        if not current_theme == 'default':
            theme_path = os.path.join(ROOT_DIR, 'themes', current_theme, 'static', path)
            if os.path.isfile(os.path.join(theme_path, filename)):
                return send_from_directory(theme_path, filename)
        static_path = os.path.join(CURRENT_DIR, 'static', path)
        return send_from_directory(static_path, filename)
    
    # Set some additional headers for non-XML and non-JSON requests
    @app.after_request
    def process_response(response):
        if request.method == 'GET':
            if response.mimetype not in ('application/json', 'application/xml'):
                response.headers['X-UA-Compatible'] = 'IE=edge'
                response.headers['Content-Security-Policy'] = "default-src 'self'; font-src 'self' https://themes.googleusercontent.com; frame-src 'none'; object-src 'none'"
                
        return response

def get_response_by_method(func, resource, method, **lookup):
    response = None
    if method in ('GET', 'HEAD'):
        response, _, _, _ = func(resource, lookup)
    elif method == 'OPTIONS':
        return app.make_default_options_response()
    else:
        abort(401)
    return response