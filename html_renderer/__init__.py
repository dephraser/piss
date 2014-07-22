import os
import simplejson as json
from flask import Flask, render_template
from data import app as data

instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')
app = Flask(__name__, static_url_path = "", instance_path=instance_path)
app.config.from_pyfile(os.path.join(instance_path, 'piss.cfg'), silent=True)

eve_client = data.test_client()
eve_domain = data.config['DOMAIN']

@app.route('/')
def get_index():
    # Redirect to an index.html page
    return render_template('index.html')

@app.route('/<resource>')
def get_resource(resource):
    if resource in eve_domain:
        return resource
    else:
        return 404

@app.route('/<resource>/<item>')
def get_item(resource, item):
    if resource in eve_domain:
        request = '/%s/%s' % (resource, item)
        r = eve_client.get(request)
        return parse_response(r)
    else:
        return 404

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
    return response

if __name__ == '__main__':
    app.run()
