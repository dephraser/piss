# -*- coding: utf-8 -*-

import os
import jinja2
import CommonMark
from flask import send_from_directory
from werkzeug.utils import secure_filename

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)


def jinja_override(app):
    # Set directory for HTML templates
    templates_path = os.path.join(CURRENT_DIR, 'templates')
    app.jinja_loader = jinja2.FileSystemLoader(templates_path)

    # Set the MarkDown -> HTML parser and renderer
    parser = CommonMark.DocParser()
    renderer = CommonMark.HTMLRenderer()

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

    @app.template_filter('parse_markdown')
    def parse_markdown(text):
        '''
        Convert the given text to HTML with the parser and renderer we've set
        up above.
        '''
        return renderer.render(parser.parse(text))

    # Add variables to the Jinja context
    # TODO: Add try... except clauses to the return statement on all of these
    # in order to fall back to the default template if a macro with the given
    # name isn't found in the loaded module.
    @app.context_processor
    def template_type_processor():
        def get_item_title(obj):
            t = app.jinja_env.get_template(get_post_template(obj))
            mod = t.make_module()
            return mod.get_item_title(obj)
        def get_item_body(obj, macros):
            t = app.jinja_env.get_template(get_post_template(obj))
            mod = t.make_module({'macros': macros})
            return mod.get_item_body(obj)
        def get_feed_item_title(obj):
            t = app.jinja_env.get_template(get_post_template(obj))
            mod = t.make_module()
            return mod.get_feed_item_title(obj)
        def get_feed_item_body(obj, macros):
            t = app.jinja_env.get_template(get_post_template(obj))
            mod = t.make_module({'macros': macros})
            return mod.get_feed_item_body(obj)
        return dict(get_item_title=get_item_title,
                    get_item_body=get_item_body,
                    get_feed_item_title=get_feed_item_title,
                    get_feed_item_body=get_feed_item_body)

    # Jinja test for lists
    def is_list(value):
        return isinstance(value, list)
    app.jinja_env.tests['list'] = is_list
    
    # Handler for the Jinja2 FunctionLoader
    def load_default_type(name):
        template_dir = os.path.join(CURRENT_DIR, 'templates')
        if 'types/' in name:
            template = os.path.join(template_dir, 'types', 'default.html')
        else:
            template = os.path.join(template_dir, 'item.html')
        with open(template, 'rb') as f:
            template_source = f.read()
        return template_source

    # Theme override
    current_theme = app.config.get('THEME', 'default')
    if not current_theme == 'default':
        theme_templates = os.path.join(ROOT_DIR, 'themes', current_theme, 'templates')
        if os.path.isdir(theme_templates):
            theme_loader = jinja2.ChoiceLoader([
                jinja2.FileSystemLoader(theme_templates),
                app.jinja_loader,
                jinja2.FunctionLoader(load_default_type)
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

def get_short_post_type(post):
    try:
        return post['type'].rstrip('/').lstrip('/').split('/')[-1]
    except KeyError:
        return 'default'

def get_post_template(post):
    return 'types/' + get_short_post_type(post) + '.html'
