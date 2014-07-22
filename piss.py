from flask import Flask
from data import app as data
from html_renderer import app as html_renderer

class ContentTypeDispatcher(object):
    """
    Mount application based on content type
    """

    def __init__(self, base_app, dispatched_app, content_types=None):
        self.base = base_app
        self.dispatched = dispatched_app
        self.dispatch_types = content_types or []

    def __call__(self, environ, start_response):
        content_type = environ.get('CONTENT_TYPE', '').lower()
        app = self.base
        for dispatch_type in self.dispatch_types:
            if content_type in dispatch_type:
                app = self.dispatched
                break
        
        return app(environ, start_response)

app = Flask(__name__)

app.wsgi_app = ContentTypeDispatcher(data, html_renderer, ['text/html'])

if __name__ == '__main__':
    app.debug = True
    app.run()