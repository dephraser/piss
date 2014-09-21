import requests
import json
from hawk.client import header as hawk_header
from hawk.client import authenticate as hawk_authenticate
from hawk.client import get_bewit as hawk_get_bewit

def main(url, method, data):
    """
    Access and modify data from a PISS server on the command line.
    """
    credentials = {
        'id': 'dh37fgj492je',
        'key': 'werxhqb98rpaxn39848xrunpaw3489ruxnpa98w4rxn',
        'algorithm': 'sha256'
    }
    ext = ''
    
    header = hawk_header(url, method, { 'credentials': credentials,
                                         'ext': ext })
    headers = get_request_headers(header['field'])
    
    if method == 'GET':
        res = requests.get(url, headers=headers)
    elif method == 'HEAD':
        res = requests.head(url, data=data, headers=headers)
    elif method == 'POST':
        res = requests.post(url, data=data, headers=headers)
    elif method == 'PATCH':
        etag = get_etag(url, headers)
        header = hawk_header(url, method, { 'credentials': credentials,
                                             'ext': ext })
        headers = get_request_headers(header['field'], etag)
        res = requests.patch(url, data=data, headers=headers)
    elif method == 'DELETE':
        etag = get_etag(url, headers)
        header = hawk_header(url, method, { 'credentials': credentials,
                                             'ext': ext })
        headers = get_request_headers(header['field'], etag)
        res = requests.delete(url, headers=headers)
    elif method == 'BEWIT':
        print("Bewit URL: ")
        print(url + '?bewit=' + hawk_get_bewit(url, {'credentials': credentials, 'ttl_sec': 60 * 1000}))
    else:
        print('Method not supported.')
        return False

    if not res.status_code in (200, 201):
        print 'Authorized request (FAILED) status=' + str(res.status_code)
    
    print(json.dumps(json.loads("".join(res.text)), sort_keys=True, indent=4))
    
    response = {'headers': res.headers}
    if hawk_authenticate(response, credentials, header['artifacts'],
                           { 'payload': res.text }):
        print "Response validates (OK)"
    else:
        print "Response validates (FAIL) " + res.text

    # print "Generating bewit url"
    # print url + '&bewit=' + client.get_bewit(url, {'credentials': credentials,
    #                                               'ttl_sec': 60 * 1000})

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
