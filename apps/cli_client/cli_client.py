import requests
import json
import os
import urlparse
from flask.config import Config
from hawk.client import header as hawk_header
from hawk.client import authenticate as hawk_authenticate
from hawk.client import get_bewit as hawk_get_bewit

def main(action, data, post_type, url, pid,  public, page):
    """
    Access and modify data from a PISS server on the command line.
    """
    current_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.splitext(os.path.basename(__file__))[0] + ".cfg"
    
    # Set up our variables
    credentials = None
    meta_url = None
    meta_post = None
    server_types = None
    res = None
    action = action.upper()
    
    if not (os.path.isfile(os.path.join(current_dir, config_file))):
        print("No configuration file found! Use `REGISTER --url <url>` to create one!")
        return False
    
    try:
        app_config = Config(current_dir)
        app_config.from_pyfile(config_file)
    except Exception as e:
        print("Could not load config from file. Use `REGISTER --url <url>` to create a new one!")
        return False
    
    try:
        credentials = app_config['CREDENTIALS']
        meta_url = app_config['META_URL']
        meta_post = app_config['META_POST']
        server_types = app_config['SERVER_TYPES']
    except Exception as e:
        print("Parameters missing from configuration file! Use `REGISTER --url <url>` to fix!")
        return False
    
    # Grab the URL from the meta post if it wasn't set
    if not url:
        url = meta_post['server']['urls']['posts_feed']
        print(url)
    
    # Add an ID to the url if specified
    if pid:
        # urlparse.urljoin was being dumb. Using os.path.join instead.
        url = os.path.join(url, pid)
    
    if action == 'GET':
        # Get rid of credentials for public queries
        if public:
            credentials = None
        res = requests.get(url, headers=get_request_headers(url, action, credentials))
    elif action == 'HEAD':
        res = requests.head(url, headers=get_request_headers(url, action, credentials))
    elif action == 'POST':
        res = requests.post(url, data=data, headers=get_request_headers(url, action, credentials))
    elif action == 'PATCH':
        etag = get_etag(url, get_request_headers(url, 'GET', credentials))
        res = requests.patch(url, data=data, headers=get_request_headers(url, action, credentials))
    elif action == 'DELETE':
        etag = get_etag(url, get_request_headers(url, 'GET', credentials))
        res = requests.delete(url, headers=get_request_headers(url, action, credentials))
    elif action == 'BEWIT':
        print("Bewit URL: ")
        print(url + '?bewit=' + hawk_get_bewit(url, {'credentials': credentials, 'ttl_sec': 60 * 1000}))
        return True
    elif action == 'NOTE':
        note_post = json.dumps({
            'entity': 'http://127.0.0.1:5000',
            'type': 'http://127.0.0.1:5000/types/note',
            'content': {
                'text': str(data)
            },
            'permissions': {'public': True},
            'app': {'name': "PISS CLI"}
        })
        res = requests.post(url, data=note_post, headers=get_request_headers(url, 'POST', credentials))
    elif action == 'REGISTER':
        if url:
            res = requests.get(url)
            if res.status_code == 200 and res.headers and 'link' in res.headers:
                meta_url = urlparse.urljoin(url, res.headers['link'])
                meta_res = requests.get(meta_url, headers={'accept': 'application/json'})
            else:
                print("Couldn't find a Link header")
                return False
            
            if meta_res.status_code == 200 and meta_res.text:
                meta_post = json.loads(meta_res.text)
            else:
                print("Couldn't get meta post at %s" % (meta_url,))
                return False
            
            if 'server' in meta_post and 'urls' in meta_post['server'] and 'types' in meta_post['server']['urls']:
                types_res = requests.get(meta_post['server']['urls']['types'], headers={'accept': 'application/json'})
            else:
                print("Incorrectly formatted meta post at %s" % (meta_post['server']['urls']['types'],))
                return False
            
            if types_res.status_code == 200 and types_res.text:
                post_types = json.loads(types_res.text)
                post_types = post_types['_items']
            else:
                print("Couldn't get list of types at %s" % (meta_post['server']['urls']['types'],))
                return False
            
            server_types = {}
            for post_type in post_types:
                server_types[post_type['name']] = post_type['schema']
            
            try:
                with open(os.path.join(current_dir, config_file), 'w+') as file:
                    file.write("META_URL = '%s'\n\n" % (str(meta_url),))
                    file.write("META_POST = %s\n\n" % (str(meta_post),))
                    file.write("SERVER_TYPES = %s\n\n" % (str(server_types),))
                    file.write("CREDENTIALS = %s\n" % (str(credentials),))
                
                print("Configuration file saved!")
                return True
            except Exception as e:
                print("Could not create or write to the configuration file.")
                return False
            
            return True
        else:
            print("You must supply the url of the entity you'd like to register with!")
            return False
    else:
        print('Method not supported.')
        return False
        
    if not res:
        return False
    
    if not res.status_code in (200, 201):
        print 'Authorized request (FAILED) status=' + str(res.status_code)
    
    try:
        print(json.dumps(json.loads("".join(res.text)), sort_keys=True, indent=4))
    except Exception as e:
        print(res.text)

def create_config_file(config_dir, config_file):
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
    root_hawk_header = hawk_header(new_post_endpoint, 'POST', { 'credentials': root_credentials })
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

def get_request_headers(url, method, credentials, etag=None):
    headers = {
        'Content-Type': 'application/json', 
        'Accept': 'application/json'
    }
    if credentials:
        header = hawk_header(url, method, { 'credentials': credentials })
        headers['Authorization'] = header['field']
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
    parser.add_argument('action', type=str, help='HTTP method or other action. Defaults to `get`.', default='get')
    parser.add_argument('data', nargs='?', type=str, help='Data to be sent to the server.', default='{}')
    parser.add_argument('--type', type=str, help='The type of post to be manipulated.', default='note')
    parser.add_argument('--url', type=str, help='URL being requested', default='')
    parser.add_argument('--id', type=str, help='ID of the resource you want to manipulate.', default='')
    parser.add_argument('--public', help='Display only public posts.', action='store_true')
    parser.add_argument('--page', help='Display the specified page of posts.', default=0)
    args = parser.parse_args()
    main(args.action, args.data, args.type, args.url, args.id, args.public, args.page)
