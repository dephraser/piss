# -*- coding: utf-8 -*-

import json
from flask import jsonify, make_response, render_template
from eve.render import render_xml
from piss.utils import get_post_by_id, request_is_json, request_is_xml


def render_response(obj, template_name, **kwargs):
    '''
    Converts a Python object into a suitable response object (JSON, XML, or
    HTML) depending on the `Accept` header of the request.

    :param obj: the object to be converted.
    :param template_name: the name of the HTML template to use.
    :param **kwargs: additional arguments for the template rendering.
    '''
    if request_is_json():
        if not isinstance(obj, dict):
            obj = {'_items': obj}
        return jsonify(obj)
    elif request_is_xml():
        response = make_response(render_xml(obj))
        response.mimetype = 'application/xml'
        response.charset = 'utf-8'
        return response
    else:
        return render_template(template_name, obj=obj, **kwargs)
