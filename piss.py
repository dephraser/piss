from werkzeug.wsgi import DispatcherMiddleware

from flask import Flask
from client import app as frontend
from server import app as backend

app = Flask( __name__ )

# Flask allows us to assign different apps to different routes while taking
# advantage of the same Python interpreter process. Here we're using the client
# as a frontend accessible at the root of the domain. The backend is our API
# server and it will be accessible at /api. 
app.wsgi_app = DispatcherMiddleware(frontend, {
    '/api':     backend
})

if __name__ == '__main__':
    app.debug = True
    app.run()