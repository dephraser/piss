import requests
import json
import os
import urlparse
from flask.config import Config
from hawk.client import header as hawk_header
from hawk.client import authenticate as hawk_authenticate
from hawk.client import get_bewit as hawk_get_bewit

def main(action, data, post_type, url, pid,  public, page, file):
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
    post_type = post_type.lower()
    
    if not (os.path.isfile(os.path.join(current_dir, config_file))) and not action == 'REGISTER':
        print("No configuration file found! Use `REGISTER --url <url>` to create one!")
        return False
    
    try:
        app_config = Config(current_dir)
        app_config.from_pyfile(config_file)
    except Exception as e:
        if not action == 'REGISTER':
            print("Could not load config from file. Use `REGISTER --url <url>` to create a new one!")
            return False
    
    try:
        credentials = app_config['CREDENTIALS']
        meta_url = app_config['META_URL']
        meta_post = app_config['META_POST']
        server_types = app_config['SERVER_TYPES']
    except Exception as e:
        if not action == 'REGISTER':
            print("Parameters missing from configuration file! Use `REGISTER --url <url>` to fix!")
            return False
    
    # Grab the URL from the meta post if it wasn't set
    if not url:
        url = meta_post['server']['urls']['posts_feed']
    
    # Add an ID to the url if specified
    if pid:
        # urlparse.urljoin was being dumb. Using os.path.join instead.
        url = os.path.join(url, pid)
    
    if action == 'GET':
        # Get rid of credentials for public queries
        if public:
            credentials = None
        # Add a page number if necessary
        if page:
            try:
                page = int(page)
                sep = '?'
                if '?' in url:
                    sep = '&'
                url += '%spage=%d' % (sep, page,)
            except Exception as e:
                pass
        res = requests.get(url, headers=get_request_headers(url, action, credentials))
    elif action == 'HEAD':
        res = requests.head(url, headers=get_request_headers(url, action, credentials))
    elif action == 'POST' and data:
        res = requests.post(url, data=data, headers=get_request_headers(url, action, credentials))
    elif action == 'POST' and post_type:
        if post_type not in server_types:
            print("Post type not found. Check TYPES to see available post types.")
            return False
        
        data = {
            'entity': meta_post['entity'],
            'type': "%s/%s" % (meta_post['server']['urls']['types'], post_type),
            'content': {},
            'app': {'name': "PISS CLI"}
        }
        recursive_input_data(data['content'], server_types[post_type])
        if public:
            data['permissions'] = {"public": True}
        
        if file:
            extra_headers = {'Content-Type': 'multipart/form-data'}
            headers = get_request_headers(url, action, credentials, extra_headers=extra_headers)
            file = open('/Users/jmontes/Desktop/dies.png', 'rb')
            files = (('dies.png', file),)
            res = requests.post(url, data=data, files=files, headers=headers)
        else:
            res = requests.post(url, data=json.dumps(data), headers=get_request_headers(url, action, credentials))
    elif action == 'PATCH':
        etag = get_etag(url, get_request_headers(url, 'GET', credentials))
        res = requests.patch(url, data=data, headers=get_request_headers(url, action, credentials, etag))
    elif action == 'DELETE':
        etag = get_etag(url, get_request_headers(url, 'GET', credentials))
        res = requests.delete(url, headers=get_request_headers(url, action, credentials, etag))
    elif action == 'BEWIT':
        print("Bewit URL: ")
        print(url + '?bewit=' + hawk_get_bewit(url, {'credentials': credentials, 'ttl_sec': 60 * 1000}))
        return True
    elif action == 'TYPES':
        print("Types available for this entity:")
        for key in server_types:
            print("* %s" % (key,))
        return True
    elif action == 'REGISTER':
        if url:
            register_app(url, os.path.join(current_dir, config_file))
            return True
        else:
            print("You must supply the url of the entity you'd like to register with!")
            return False
    elif action == 'UPDATE':
        try:
            server_types = get_server_types(meta_post)
            write_config_file(os.path.join(current_dir, config_file), meta_url, meta_post, server_types, credentials)
            return True
        except Exception as e:
            print("Could not update configuration!")
            return False
    else:
        print('Method not supported.')
        return False
    
    if not res.status_code in (200, 201):
        print 'Authorized request (FAILED) status=' + str(res.status_code)
    
    try:
        print(json.dumps(json.loads("".join(res.text)), sort_keys=True, indent=4))
    except Exception as e:
        print(res.text)

def register_app(url, config_path):
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
    
    server_types = get_server_types(meta_post)
    
    print("Credentials needed before being able to create an app post.")
    cid = raw_input("Credentials ID: ")
    algorithm = raw_input("Algorithm: ")
    key = raw_input("Key: ")
    
    input_credentials = {
        'id': cid,
        'algorithm': algorithm,
        'key': key
    }
    
    # Create an app post on the server and retrieve the app's credentials
    credentials = get_app_credentials(input_credentials, meta_post)
    
    write_config_file(config_path, meta_url, meta_post, server_types, credentials)
    
    return True

def get_app_credentials(input_credentials, meta_post):
    entity = meta_post['entity']
    types_endpoint = meta_post['server']['urls']['types']
    new_post_endpoint = meta_post['server']['urls']['new_post']
    
    # Attempt to create an app post on the server
    app_post = get_app_post(entity, types_endpoint)
    input_headers = get_request_headers(new_post_endpoint, 'POST', input_credentials)
    input_res = requests.post(new_post_endpoint, data=app_post, headers=input_headers)
    if not input_res.status_code == 201:
        print("Could not create app post. Server returned: %s" % (input_res.text,))
        return False
    
    # Attempt to get the link header
    try:
        link_header = input_res.headers['link']
        if not str(types_endpoint + "/credentials") in link_header:
            print("Could not retrieve credentials URL. Link header contains: %s" % (link_header,))
            return False
    except Exception as e:
        print("Could not understand server headers. Server returned: %s" % (root_res.headers,))
        return False
    
    # Attempt to get the credentials post
    credentials_url = link_header[link_header.find("<")+1:link_header.find(">")]
    
    # We need to create the root headers again because they depend on the URL
    input_headers = get_request_headers(credentials_url, 'GET', input_credentials)
    cred_res = requests.get(credentials_url, headers=input_headers)
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
    
    return credentials

def get_server_types(meta_post):
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
    
    return server_types

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

def write_config_file(config_path, meta_url, meta_post, server_types, credentials):
    try:
        with open(config_path, 'w+') as file:
            file.write("META_URL = '%s'\n\n" % (str(meta_url),))
            file.write("META_POST = %s\n\n" % (str(meta_post),))
            file.write("SERVER_TYPES = %s\n\n" % (str(server_types),))
            file.write("CREDENTIALS = %s\n" % (str(credentials),))
        
        print("Configuration file saved!")
        return True
    except Exception as e:
        print("Could not create or write to the configuration file.")
        return False

def get_request_headers(url, method, credentials, etag=None, extra_headers=None):
    headers = {
        'Content-Type': 'application/json', 
        'Accept': 'application/json'
    }
    if extra_headers:
        for key in extra_headers:
            headers[key] = extra_headers[key]
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

def recursive_input_data(data, schema, parent=""):
    for key in schema:
        key_string = key
        if parent:
            key_string = "%s.%s" % (parent, key,)
        if 'required' in schema[key] and schema[key]['required']:
            key_string += "*"
        
        if schema[key]['type'] == 'string':
            value = raw_input("%s: " % (key_string,))
        elif schema[key]['type'] == 'integer':
            value = int(raw_input("%s: " % (key_string,)))
        elif schema[key]['type'] == 'dict':
            value = recursive_input_data({}, schema[key]['schema'], key)
        elif schema[key]['type'] == 'list':
            value = []
            counter = 0
            list_item = int(raw_input("%s[%d]: " % (key_string, counter,)))
            while list_item:
                value.append(list_item)
                counter += 1
                list_item = int(raw_input("%s[%d]: " % (key_string, counter,)))
        
        if value:
            data[key] = value
    
    return data

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='CLI interface for a PISS instance.')
    parser.add_argument('action', type=str, help='HTTP method or other action. Defaults to `get`.', default='get')
    parser.add_argument('data', nargs='?', type=str, help='Data to be sent to the server.', default=None)
    parser.add_argument('--type', type=str, help='The type of post to be manipulated.', default='')
    parser.add_argument('--url', type=str, help='URL being requested', default='')
    parser.add_argument('--id', type=str, help='ID of the resource you want to manipulate.', default='')
    parser.add_argument('--public', help='Display only public posts.', action='store_true')
    parser.add_argument('--page', help='Display the specified page of posts.', default=0)
    parser.add_argument('--file', help='A file to be uploaded', default='')
    args = parser.parse_args()
    main(args.action, args.data, args.type, args.url, args.id, args.public, args.page, args.file)
