import os
import simplejson as json
from flask import Flask, render_template
from data import app as data
import requests

from hawk.client import header as hawk_header
from hawk.client import authenticate as hawk_authenticate

instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')
app = Flask(__name__, instance_path = instance_path)
app.config.from_pyfile(os.path.join(instance_path, 'piss.cfg'), silent=True)

eve_domain = data.config['DOMAIN']

credentials = {
    'id': 'dh37fgj492je',
    'key': 'werxhqb98rpaxn39848xrunpaw3489ruxnpa98w4rxn',
    'algorithm': 'sha256'
}

@app.route('/')
def get_index():
    # Redirect to an index.html page
    return render_template('index.html')

@app.route('/<resource>')
def get_resource(resource):
    if resource in eve_domain:
        return resource
    else:
        return 'This page does not exist', 404

@app.route('/<resource>/<item>')
def get_item(resource, item):
    if resource in eve_domain:
        url = 'http://127.0.0.1:5000/%s/%s' % (resource, item)
        header = hawk_header(url, 'GET', { 'credentials': credentials,
                                             'ext': '' })
        headers = {'Authorization': header['field'], 'Content-Type': 'application/json', 'Accept': 'application/json'}
        res = requests.get(url, headers=headers)
        return res.text, res.status_code
    else:
        return 'This page does not exist', 404

def parse_response(r):
    try:
        v = json.loads(r.get_data())
    except json.JSONDecodeError:
        v = None
    if v:
        return v, r.status_code
    else:
        return r

@app.after_request
def process_response(response):
    response.headers['X-UA-Compatible'] = 'IE=edge'
    response.headers['Content-Security-Policy'] = "default-src 'self'; font-src 'self' https://themes.googleusercontent.com; frame-src 'none'; object-src 'none'"
    return response

if __name__ == '__main__':
    app.run()
