
from bottle import get, route, request, run, template, static_file, jinja2_view, jinja2_template

from config import general as config

WEB_ROOT = 'www/'

@route('/static/js/<path:path>')
def javascripts(path):
    return static_file(path, root=WEB_ROOT + 'static/js')

@route('/static/css/<path:path>')
def stylesheets(path):
    print('static')
    return static_file(path, root=WEB_ROOT + 'static/css')

@route('/static/fonts/<path:path>')
def fonts(path):
    return static_file(path, root=WEB_ROOT + 'static/fonts')

@route('/static/img/<path:path>')
def stylesheets(path):
    return static_file(path, root=WEB_ROOT + 'static/img')

@route('/')
@jinja2_view('main.html', template_lookup=[WEB_ROOT + 'templates'])#, getRoot=getRoot)
def home():
    return {}


def start(host, port, debug=False):
    run(host=host, port=port, reloader=debug)

