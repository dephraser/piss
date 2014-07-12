from flask import Flask, render_template

app = Flask(__name__, static_url_path = "", instance_relative_config=True)
app.config.from_pyfile('piss.cfg', silent=True)

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
