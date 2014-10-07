# -*- coding: utf-8 -*-

import os
import shutil
import hashlib
from flask import current_app
from werkzeug import secure_filename

ONE_MB = 1024 * 1024

def save_attachment(file):
    '''
    Saves a file upload to the server and returns an attachments object.
    '''
    attachments_path = get_attachments_path()
    tmp_path = get_temp_path()
    
    filename = secure_filename(file.filename)
    tmp_file = os.path.join(tmp_path, filename)
    file.save(tmp_file)
    
    size = os.stat(tmp_file).st_size
    digest = get_file_digest(tmp_file)
    content_type = file.mimetype if file.mimetype else file.content_type.split(';')[0]
    
    tree_path = os.path.join(get_tree_path(attachments_path, digest), digest)
    shutil.move(tmp_file, tree_path)
    
    return {
        'content_type': content_type,
        'name': filename,
        'digest': digest,
        'size': size
    }
    
def get_attachment(attachment_obj):
    '''
    Retrieves a file object based on attachment information.
    '''
    attachments_path = get_attachments_path()
    digest = attachment_obj['digest']
    return os.path.join(get_tree_path(attachments_path, digest), digest)
    

def delete_attachment(attachment_obj):
    '''
    Delete a file object from the server based on attachment information.
    '''
    attachments_path = get_attachments_path()
    digest = attachment_obj['digest']
    os.unlink(os.path.join(get_tree_path(attachments_path, digest), digest))

def get_attachments_path():
    '''
    Get the path where attachments are saved based on the current app context.
    '''
    return os.path.join(current_app.instance_path, 'attachments')

def get_tree_path(base_dir, word, subdirs=3):
    '''
    Get the full path of a directory where the names of the subdirectories are
    determined based on the characters of a given word.
    '''
    tree_path = ''
    for i in range(subdirs):
        tree_path += word[i] + '/'
    tree_path = os.path.join(base_dir, tree_path[:-1])
    if not os.path.isdir(tree_path):
        os.makedirs(tree_path)
    return tree_path

def get_temp_path():
    '''
    Get the path where temporary files are saved in the current app context.
    '''
    return os.path.join(current_app.instance_path, 'tmp')

def get_file_digest(file_path):
    with file(file_path, 'r') as f:
        hasher = hashlib.sha512()
        while True:
            r = f.read(ONE_MB)
            if not len(r):
                break
            hasher.update(r)
    # Hex-encoded first 256 bits of the SHA-512
    return format((long(hasher.hexdigest(), 16) >> 256), 'x')
    