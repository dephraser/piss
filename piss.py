from flask import Flask
from data import app as data
from html_renderer import app as html_renderer

class AcceptTypeDispatcher(object):
    """
    Mount application based on 'Accept' in the request header.
    """

    def __init__(self, default_app, dispatched_app, content_types=None):
        self.default = default_app
        self.dispatched = dispatched_app
        self.dispatch_types = content_types or []

    def __call__(self, environ, start_response):
        accept_type = environ.get('HTTP_ACCEPT', '').lower()
        app = self.default
        for dispatch_type in self.dispatch_types:
            if dispatch_type in accept_type:
                app = self.dispatched
                break
        return app(environ, start_response)

app = Flask(__name__)

app.wsgi_app = AcceptTypeDispatcher(data, html_renderer, ['text/html'])

if __name__ == '__main__':
    app.debug = True
    app.run()