
from bottle import get, route, request, run, template, static_file, jinja2_view, jinja2_template

from config import general as config

@route('/')
@jinja2_view('main.html', template_lookup=['templates'])#, getRoot=getRoot)
def home(todo=None):
    return {}

def start(host, port):
    run(host=host, port=port)

