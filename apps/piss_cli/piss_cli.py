#!/usr/bin/env python

import json
import os
import mimetypes
import click
import requests
from requests_toolbelt import MultipartEncoder
from flask.config import Config
from hawk.client import header as hawk_header
from hawk.client import get_bewit as hawk_get_bewit


@click.group()
@click.pass_context
def cli(ctx):
    '''
    Access and modify data from a PISS server on the command line.
    '''
    current_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = os.path.splitext(os.path.basename(__file__))[0] + ".cfg"

    ctx.obj = {}
    ctx.obj['current_dir'] = current_dir
    ctx.obj['config_file'] = config_file

    if ctx.args[0] != 'register':
        if not os.path.isfile(os.path.join(current_dir, config_file)):
            click.echo('No configuration file found! Use `register <url>`  to\
 create one!')
            ctx.abort()

        try:
            app_config = Config(current_dir)
            app_config.from_pyfile(config_file)
        except Exception as e:
            click.echo('Could not load config from file. Use `register <url>`\
 to create a new one!')
            ctx.abort()

        try:
            ctx.obj['credentials'] = app_config['CREDENTIALS']
            ctx.obj['meta_url'] = app_config['META_URL']
            meta_post = app_config['META_POST']
            ctx.obj['meta_post'] = meta_post
            ctx.obj['url'] = meta_post['server']['urls']['posts_feed']
        except Exception as e:
            click.echo('Parameters missing from configuration file! Use\
 `register <url>` to fix!')
            ctx.abort()


@cli.command()
@click.pass_obj
@click.argument('post_type')
@click.option('--public', default=False, is_flag=True, help='Create a public post.')
@click.option('--file', default=None, help='Attachment for the post.')
def new(ctx, post_type, public, file):
    '''
    Creates a new post of the given type.
    '''
    if post_type not in SUPPORTED_TYPES:
        click.echo("Post type not found. Check 'types' to see available post types.")
        return False

    meta_post = ctx['meta_post']
    data = {
        'entity': meta_post['entity'],
        'type': "%s/types/%s" % (meta_post['entity'], post_type),
        'content': {},
        'app': {'name': "PISS CLI"}
    }
    if public:
        data['permissions'] = {"public": True}
    data['content'] = recursive_input_data(SUPPORTED_TYPES[post_type])
    if file:
        file_data = (os.path.basename(file), open(file, 'rb'), mimetypes.guess_type(file)[0])
        m = MultipartEncoder(fields={'message': json.dumps(data), 'file': file_data})
        extra_headers = {'Content-Type': m.content_type}
        data = m
    else:
        extra_headers = None
        data = json.dumps(data)
    headers = get_request_headers(ctx['url'], 'POST', ctx['credentials'], extra_headers=extra_headers)
    res = requests.post(ctx['url'], data=data, headers=headers)
    response_handler(res)


@cli.command()
@click.pass_obj
@click.argument('service')
@click.argument('post_id')
@click.argument('message', default=None, required=False)
def syndicate(ctx, service, post_id, message):
    '''
    Syndicate a post to the given service.
    '''
    SERVICES = {
        'twitter': 'https://twitter.com',
        'facebook': 'https://www.facebook.com'
    }
    try:
        synd_entity = SERVICES[service]
    except KeyError:
        click.echo('The service "%s" is not available.' % (service,))
        return False
    ctx['url'] = os.path.join(ctx['url'], post_id)

    # Syndicated posts MUST be public
    res = requests.get(ctx['url'],
                       headers=get_request_headers(ctx['url'], 'GET', None))
    status_code = int(res.status_code)
    if status_code < 200 or status_code >= 300:
        click.echo('Post not accessible. Status: %d' % (status_code,))
        return False
    post = res.json()

    entity = ctx['meta_post']['entity']
    post_type = post['type']
    if message:
        post_type = os.path.join(entity, 'types', 'note')
    else:
        message = post['content']['text']
    data = {
        'entity': synd_entity,
        'type': post_type,
        'content': {
            'text': message
        },
        'links': [{'post': post['_id']}]
    }
    synd_url = os.path.join(entity, 'syndicate', service)
    headers = get_request_headers(synd_url, 'POST', ctx['credentials'])
    res = requests.post(synd_url, data=json.dumps(data), headers=headers)
    response_handler(res)


@cli.command()
@click.pass_obj
@click.argument('post_id', default=None, required=False)
@click.option('--url', default='', help='URL being requested.')
@click.option('--page', default=0, help='Display the specified page of posts.')
@click.option('--public', default=False, is_flag=True, help='Display only public posts.')
def get(ctx, url, post_id, page, public):
    '''
    Retrieve the given post ID.
    '''
    if url:
        ctx['url'] = url
    if public:
        ctx['credentials'] = None
    if post_id:
        ctx['url'] = os.path.join(ctx['url'], post_id)
    if page:
        try:
            sep = '?'
            if '?' in ctx['url']:
                sep = '&'
            ctx['url'] += '%spage=%d' % (sep, page,)
        except Exception as e:
            pass
    res = requests.get(ctx['url'], headers=get_request_headers(ctx['url'], 'GET', ctx['credentials']))
    response_handler(res)


@cli.command()
@click.pass_obj
@click.argument('post_id', default=None, required=False)
@click.option('--url', default='', help='URL being requested.')
def head(ctx, url, post_id):
    '''
    Perform a HEAD request on the given post ID.
    '''
    if url:
        ctx['url'] = url
    if post_id:
        ctx['url'] = os.path.join(ctx['url'], post_id)
    res = requests.head(ctx['url'], headers=get_request_headers(ctx['url'], 'HEAD', ctx['credentials']))
    try:
        click.echo(json.dumps(dict(res.headers), sort_keys=True, indent=4))
    except Exception as e:
        click.echo(dict(res.headers))


@cli.command()
@click.pass_obj
@click.argument('data')
@click.option('--url', default='', help='URL being POSTed to.')
def post(ctx, url, data):
    '''
    Perform a POST request with the given data.
    '''
    if url:
        ctx['url'] = url
    res = requests.post(ctx['url'], data=data, headers=get_request_headers(ctx['url'], 'POST', ctx['credentials']))
    response_handler(res)


@cli.command()
@click.pass_obj
@click.argument('post_id', default=None, required=False)
@click.argument('data')
@click.option('--url', default='', help='URL being POSTed to.')
def patch(ctx, url, post_id, data):
    '''
    Perform a PATCH with a post ID and data.
    '''
    if not url and not post_id:
        click.echo('A URL or post ID must be provided.')
        return False
    if url:
        ctx['url'] = url
    if post_id:
        ctx['url'] = os.path.join(ctx['url'], post_id)
    try:
        etag = get_etag(ctx['url'], get_request_headers(ctx['url'], 'GET', ctx['credentials']))
    except Exception as e:
        click.echo('Could not get etag for post at URL %s' % (ctx['url'],))
        return False
    res = requests.patch(ctx['url'], data=data, headers=get_request_headers(ctx['url'], 'PATCH', ctx['credentials'], etag))
    response_handler(res)


@cli.command()
@click.pass_obj
@click.argument('post_id', default=None, required=False)
@click.option('--url', default='', help='URL being POSTed to.')
def delete(ctx, url, post_id):
    '''
    Perform a DELETE request on a given post ID.
    '''
    if not url and not post_id:
        click.echo('A URL or post ID must be provided.')
        return False
    if url:
        ctx['url'] = url
    if post_id:
        ctx['url'] = os.path.join(ctx['url'], post_id)
    try:
        etag = get_etag(ctx['url'], get_request_headers(ctx['url'], 'GET', ctx['credentials']))
    except Exception as e:
        click.echo('Could not get etag for post at URL %s' % (ctx['url'],))
        return False
    res = requests.delete(ctx['url'], headers=get_request_headers(ctx['url'], 'DELETE', ctx['credentials'], etag))
    response_handler(res)


@cli.command()
@click.pass_obj
@click.argument('url')
@click.option('--ttl', default=60, show_default=True, help='Duration of bewit in minutes.')
def bewit(ctx, url, ttl):
    '''
    Create a bewit for the given URL.
    '''
    url = url.rstrip('/')
    if url == ctx['meta_post']['server']['urls']['posts_feed'] or url == ctx['meta_post']['entity']:
        click.echo("Use bewits only for specific posts!")
        return False
    if '?' in url:
        click.echo("Can't make bewits for queries!")
        return False
    click.echo("Bewit URL: ")
    click.echo(url + '?bewit=' + hawk_get_bewit(url, {'credentials': ctx['credentials'], 'ttl_sec': ttl * 60}))


@cli.command()
@click.pass_obj
def types(ctx):
    '''
    List the available post types at this entity.
    '''
    click.echo("Types available for this entity:")
    for key in SUPPORTED_TYPES:
        click.echo("  * %s" % (key,))


@cli.command()
@click.argument('url')
@click.pass_obj
def register(ctx, url):
    '''
    Register this application at an entity URL.
    '''
    if register_app(url, os.path.join(ctx['current_dir'],
                    ctx['config_file'])):
        click.echo('Registration success!')
    else:
        click.echo('Registration failure.')


def register_app(url, config_path):
    res = requests.get(url)
    if res.status_code == 200 and res.headers and 'link' in res.headers and 'meta-post' in res.headers['link']:
        # Link headers *may* be a list of comma-separated values...
        split_links = res.headers['link'].split(',')
        meta_url = ''
        for split_link in split_links:
            if 'meta-post' in split_link:
                # Meta post links have the format `<url>; rel="meta-post"`
                meta_url = split_link.split(';')[0]
                break
        meta_res = requests.get(meta_url, headers={'accept': 'application/json'})
    else:
        click.echo("Couldn't find a Link header")
        return False

    if meta_res.status_code == 200 and meta_res.text:
        meta_post = json.loads(meta_res.text)
    else:
        click.echo("Couldn't get meta post at %s" % (meta_url,))
        return False

    click.echo("Credentials needed before being able to create an app post.")
    cid = click.prompt("Credentials ID", type=str)
    algorithm = click.prompt("Algorithm", type=str)
    key = click.prompt("Key", type=str)

    input_credentials = {
        'id': str(cid),
        'algorithm': str(algorithm),
        'key': str(key)
    }

    # Create an app post on the server and retrieve the app's credentials
    credentials = get_app_credentials(input_credentials, meta_post)
    if credentials:
        write_config_file(config_path, meta_url, meta_post, credentials)
    else:
        click.echo("Couldn't get credentials! Exiting...")
        return False

    return True


def get_app_credentials(input_credentials, meta_post):
    entity = meta_post['entity']
    types_endpoint = meta_post['entity'] + "/types"
    new_post_endpoint = meta_post['server']['urls']['new_post']

    # Attempt to create an app post on the server
    app_post = get_app_post(entity, types_endpoint)
    input_headers = get_request_headers(new_post_endpoint, 'POST', input_credentials)
    input_res = requests.post(new_post_endpoint, data=app_post, headers=input_headers)

    if not input_res.status_code == 201:
        click.echo("Could not create app post. Server returned: \n%s\n%s" % (input_res.headers, input_res.text,))
        return False

    # Attempt to get the link header
    try:
        link_header = input_res.headers['link']
        if not str(types_endpoint + "/credentials") in link_header:
            click.echo("Could not retrieve credentials URL. Link header contains: %s" % (link_header,))
            return False
    except Exception as e:
        click.echo("Could not understand server headers. Server returned: \n%s\n%s" % (input_res.headers, input_res.text,))
        return False

    # Attempt to get the credentials post
    credentials_url = link_header[link_header.find("<")+1:link_header.find(">")]

    # Hopefully the credentials URL has a proper bewit
    cred_res = requests.get(credentials_url, headers=get_request_headers(credentials_url, 'GET', None))
    if not cred_res.status_code == 200:
        click.echo("Could not get credentials post. Server returned: \n%s\n%s" % (str(cred_res.headers), cred_res.text,))
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
        click.echo("Could not create credentials object.")
        return False

    return credentials


def write_config_file(config_path, meta_url, meta_post, credentials):
    try:
        with open(config_path, 'w+') as file:
            file.write("META_URL = '%s'\n\n" % (str(meta_url),))
            file.write("META_POST = %s\n\n" % (str(meta_post),))
            file.write("CREDENTIALS = %s\n" % (str(credentials),))

        click.echo("Configuration file saved!")
        return True
    except Exception as e:
        click.echo("Could not create or write to the configuration file.")
        return False


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
    return res['_etag']


def response_handler(response):
    status_code = int(response.status_code)
    if status_code < 200 or status_code >= 300:
        click.echo('Request failed. Status: %d' % (status_code,))
        click.echo(str(response.text))
        return False

    try:
        if len(response.text):
            click.echo(json.dumps(json.loads("".join(response.text)), sort_keys=True, indent=4))
        else:
            click.echo('%d: (Empty response)' % (status_code,))
    except Exception as e:
        click.echo(response.text)


def recursive_input_data(schema, parent=""):
    data = {}
    types = {
        'string': unicode,
        'integer': int,
        'dict': dict,
        'list': list
    }
    for key in schema:
        value = None
        key_string = key
        required = False
        default = ''
        t = schema[key]['type']
        if parent:
            key_string = "%s.%s" % (parent, key,)
        if 'required' in schema[key] and schema[key]['required']:
            key_string += "*"
            required = True
            default = None
        if t == 'string' or t == 'integer':
            value = click.prompt(key_string, default=default, show_default=False, type=types[t])
        elif schema[key]['type'] == 'dict':
            if required or click.confirm('Specify %s?' % (key_string,)):
                value = recursive_input_data(schema[key]['schema'], key)
        elif schema[key]['type'] == 'list':
            if required or click.confirm('Specify %s?' % (key_string,)):
                value = []
                counter = 0
                get_input = True
                list_type = str
                if 'schema' in schema[key]:
                    while get_input:
                        list_type = types[schema[key]['schema']['type']]
                        list_item = click.prompt("%s[%d]" % (key_string, counter), default=default, show_default=False, type=list_type)
                        if not list_item:
                            get_input = False
                            break
                        value.append(list_item)
                        counter += 1
                elif 'items' in schema[key]:
                    items = []
                    for idx, item in enumerate(schema[key]['items']):
                        list_type = types[item['type']]
                        list_item = click.prompt("%s[%d]" % (key_string, idx), default=default, show_default=False, type=list_type)
                        if list_item:
                            items.append(list_item)
                    if len(items):
                        value = items
                    else:
                        value = None
        if value:
            data[key] = value
    return data

SUPPORTED_TYPES = {
    'note': {
        'location': {
            'schema': {
                'coordinates': {
                    'items': [
                        {'type': 'integer'}, 
                        {'type': 'integer'}
                    ], 
                    'required': True, 
                    'type': 'list'
                }, 
                'name': {
                    'type': 'string'
                }, 
                'type': {
                    'allowed': ['Point'], 
                    'required': True, 
                    'type': 'string'
                }
            }, 
            'type': 'dict'
        }, 
        'text': {
            'type': 'string'
        }
    }
}

if __name__ == '__main__':
    cli()
