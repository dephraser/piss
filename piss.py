from flask import Flask
from data import app as data
from html_renderer import app as html_renderer

class DataTypeDispatcher(object):
    """
    Mount application based on 'Accept' or 'Content-Type' in the request header.
    """

    def __init__(self, default_app, dispatched_app, content_types=None):
        self.default = default_app
        self.dispatched = dispatched_app
        self.dispatch_types = content_types or []

    def __call__(self, environ, start_response):
        accept_type = environ.get('HTTP_ACCEPT', '').lower()
        content_type = environ.get('CONTENT_TYPE', '').lower()
        app = self.default
        for dispatch_type in self.dispatch_types:
            if accept_type.startswith(dispatch_type) or content_type.startswith(dispatch_type):
                app = self.dispatched
                break
        return app(environ, start_response)

app = Flask(__name__)

app.wsgi_app = DataTypeDispatcher(html_renderer, data, ['application/json', 'application/xml'])

if __name__ == '__main__':
    app.debug = True
    app.run()