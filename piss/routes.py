# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, current_app, make_response, render_template
from eve.render import render_xml
from html_renderer.decorators import request_is_json, request_is_xml

server = Blueprint('server', __name__)

@server.route('/meta')
def meta():
    if request_is_json():
        return jsonify(current_app.config['META_POST'])
    elif request_is_xml():
        response = make_response(render_xml(current_app.config['META_POST']))
        response.mimetype = 'application/xml'
        response.charset = 'utf-8'
        return response
    else:
        return render_template('meta.html', item=current_app.config['META_POST'])
