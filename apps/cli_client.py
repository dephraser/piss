import requests
import json
import os
from flask.config import Config
from hawk.client import header as hawk_header
from hawk.client import authenticate as hawk_authenticate
from hawk.client import get_bewit as hawk_get_bewit

def main(url, method, data):
    """
    Access and modify data from a PISS server on the command line.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.splitext(os.path.basename(__file__))[0] + ".cfg"
    instance_path = os.path.join(os.path.dirname(current_dir), 'instance')
    
    try:
        app_config = Config(instance_path)
        app_config.from_pyfile(config_file)
        credentials = app_config['CREDENTIALS']
    except Exception as e:
        create_config = raw_input("No configuration file found! Create one? [y/n]\n").lower()
        if not create_config == 'y':
            print("Exiting.")
            return False
        
        credentials = create_config_file(instance_path, config_file)
    
    # Make sure the config is a dict
    if not credentials or type(credentials) is not dict:
        print("Credentials object not loaded properly. Check config.")
        return False
    
    # Construct headers for our request
    header = hawk_header(url, method, { 'credentials': credentials })
    headers = get_request_headers(header['field'])
    
    if method == 'GET':
        res = requests.get(url, headers=headers)
    elif method == 'HEAD':
        res = requests.head(url, data=data, headers=headers)
    elif method == 'POST':
        res = requests.post(url, data=data, headers=headers)
    elif method == 'PATCH':
        etag = get_etag(url, headers)
        header = hawk_header(url, method, { 'credentials': credentials })
        headers = get_request_headers(header['field'], etag)
        res = requests.patch(url, data=data, headers=headers)
    elif method == 'DELETE':
        etag = get_etag(url, headers)
        header = hawk_header(url, method, { 'credentials': credentials })
        headers = get_request_headers(header['field'], etag)
        res = requests.delete(url, headers=headers)
    elif method == 'BEWIT':
        print("Bewit URL: ")
        print(url + '?bewit=' + hawk_get_bewit(url, {'credentials': credentials, 'ttl_sec': 60 * 1000}))
        return True
    else:
        print('Method not supported.')
        return False

    if not res.status_code in (200, 201):
        print 'Authorized request (FAILED) status=' + str(res.status_code)
    
    try:
        print(json.dumps(json.loads("".join(res.text)), sort_keys=True, indent=4))
    except Exception as e:
        print(res.text)
    
    response = {'headers': res.headers}
    if hawk_authenticate(response, credentials, header['artifacts'],
                           { 'payload': res.text }):
        print "Response validates (OK)"
    else:
        print "Response validates (FAIL) " + res.text

def create_config_file(instance_path, config_file):
    # Assume the PISS instance config file is in the usual location
    piss_config = Config(instance_path)
    piss_config.from_pyfile('piss.cfg')
    
    # Attempt to load configuration options from PISS instance
    try:
        root_credentials = piss_config['ROOT_CREDENTIALS']
        entity = piss_config['META_POST']['entity']
        types_endpoint = piss_config['META_POST']['server']['urls']['types']
        new_post_endpoint = piss_config['META_POST']['server']['urls']['new_post']
    except Exception as e:
        print("Could not load credentials from PISS instance.")
        return False
    
    # Attempt to create an app post on the server
    app_post = get_app_post(entity, types_endpoint)
    root_hawk_header = hawk_header(url, 'POST', { 'credentials': root_credentials })
    root_headers = get_request_headers(root_hawk_header['field'])
    root_res = requests.post(new_post_endpoint, data=app_post, headers=root_headers)
    if not root_res.status_code == 201:
        print("Could not create app post. Server returned: %s" % (root_res.text,))
        return False
    
    # Attempt to get the link header
    try:
        link_header = root_res.headers['link']
        if not str(types_endpoint + "/credentials") in link_header:
            print("Could not retrieve credentials URL. Link header contains: %s" % (link_header,))
            return False
    except Exception as e:
        print("Could not understand server headers. Server returned: %s" % (root_res.headers,))
        return False
    
    # Attempt to get the credentials post
    credentials_url = link_header[link_header.find("<")+1:link_header.find(">")]
    # We need to create the root headers again because they depend on the URL
    root_hawk_header = hawk_header(credentials_url, 'GET', { 'credentials': root_credentials })
    root_headers = get_request_headers(root_hawk_header['field'])
    cred_res = requests.get(credentials_url, headers=root_headers)
    if not cred_res.status_code == 200:
        print("Could not get credentials post. Server returned: %s" % (cred_res.text,))
        return False
    
    # Attempt to create credentials from the credentials post
    try:
        cred_obj = json.loads("".join(cred_res.text))
        credentials = {
            'id': str(cred_obj['_id']),
            'key': str(cred_obj['content']['hawk_key']),
            'algorithm': str(cred_obj['content']['hawk_algorithm'])
        }
    except Exception as e:
        print("Could not create credentials object.")
        return False
    
    # Attempt to create a configuration file from the credentials post
    try:
        with open(os.path.join(instance_path, config_file), 'w+') as file:
            file.write("CREDENTIALS = %s" % (str(credentials),))
    except Exception as e:
        print("Could not create or write to the configuration file.")
        return False
    
    return credentials

def get_app_post(entity, types_endpoint):
    return json.dumps({
    	'entity': str(entity),
    	'type': str(types_endpoint) + "/app",
    	'content': {
    		'name': "PISS CLI",
    		'description': "CLI client for PISS",
    		'url': "localhost",
    		'redirect_url': "localhost"
    	}
    })

def get_request_headers(auth, etag=None):
    headers = {
        'Authorization': auth, 
        'Content-Type': 'application/json', 
        'Accept': 'application/json'
    }
    if etag:
        headers['If-Match'] = etag
    
    return headers

def get_etag(url, headers):
    res = requests.get(url, headers=headers)
    res = json.loads(res.text)
    
    if type(res) is dict and '_etag' in res:
        etag = res['_etag']
    else:
        print("Bad item")
        return False
    
    return etag

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='CLI interface for a PISS instance.')
    parser.add_argument('url', type=str, help='URL of the resource.')
    parser.add_argument('method', nargs='?', type=str, help='HTTP method. Defaults to `GET`.', default='GET')
    parser.add_argument('data', nargs='?', type=str, help='Data to be sent to the server.', default='{}')
    args = parser.parse_args()
    main(args.url, args.method, args.data)
