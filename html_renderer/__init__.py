import os
from flask import Flask, render_template

instance_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'instance')
app = Flask(__name__, static_url_path = "", instance_path=instance_path)
app.config.from_pyfile(os.path.join(instance_path, 'piss.cfg'), silent=True)

@app.route('/')
def get_index():
    # Redirect to an index.html page
    return render_template('index.html')
    
@app.after_request
def process_response(response):
    response.headers['X-UA-Compatible'] = 'IE=edge'
    return response

if __name__ == '__main__':
    app.run()
