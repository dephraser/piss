from flask import Flask

app = Flask(__name__, static_url_path = "")

@app.route('/')
def get_index():
    # Redirect to an index.html page
    return app.send_static_file('index.html')
    
@app.after_request
def process_response(response):
    response.headers['X-UA-Compatible'] = 'IE=edge,chrome=1'
    return response

if __name__ == '__main__':
    app.debug = True
    app.run()