import os
import flask
import markdown
import functools
import flask_cors
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from gevent.wsgi import WSGIServer

BLOG_FOLDER = 'posts'
DEBUG = False

if __name__ == '__main__':
    blogger = flask.Flask(__name__, static_folder=BLOG_FOLDER)
    flask_cors.CORS().init_app(blogger)
else:
    blogger = flask.Blueprint('blogger', __name__, static_folder=BLOG_FOLDER)

BLOG_PATH = blogger.static_folder


@blogger.route('/blog_posts/<path:selection>')
@functools.lru_cache(2 ** 10)
def post_view(selection):
    '''
    returns dynamically the html of the given blog page
    '''

    for absolute, relative in resource_paths():
        if relative.replace('.md', '') == selection:
            return flask.jsonify(post_fetcher(absolute))

    return flask.jsonify(error=404, text='unable to find post'), 404


@blogger.route('/get_blog_routes')
@functools.lru_cache(2 ** 8)
def get_blog_routes():
    '''
    returns a list of all the URIs for blog posts
    '''
    uris = []
    for absolute, relative in resource_paths():
        uris.append(relative.replace('.md', ''))
    return flask.jsonify(uris)


def resource_paths():
    '''
    returns a generator of tuples of the absolute path and relative path of
    every markdown resource
    '''
    for path, _, files in os.walk(BLOG_PATH):
        for name in files:
            absolute_path = os.path.join(path, name)
            relative_path = os.path.relpath(absolute_path, blogger.static_folder)
            yield absolute_path, relative_path


def create_dir():
    '''
    looks for the directory where we store blog posts, and if it
    doesnt exist creates it
    '''

    try:
        os.stat(BLOG_PATH)
    except OSError:
        os.makedirs(BLOG_PATH)


def post_fetcher(path):
    with open(path, 'r') as markdown_file:
        try:
            return markdown.markdown(markdown_file.read())
        except:
            return '<h2> An error occured on the server</h2>'


class ReloadFiles(FileSystemEventHandler):
    '''
    simple class to watch for changes in the blog posts and reload accordingly
    '''

    def on_any_event(self, event):
        create_dir()
        post_view.cache_clear()
        get_blog_routes.cache_clear()


def start_watcher():
    '''
    starts a watcher in the background that reloads markdown templates if
    a change is made
    '''
    event_handler = ReloadFiles()
    observer = Observer()
    observer.schedule(event_handler, BLOG_PATH, recursive=True)
    observer.start()


if __name__ == '__main__':
    create_dir()
    start_watcher()
    if DEBUG:
        blogger.run(port=8080, host='0.0.0.0')
    else:
        http_server = WSGIServer(('0.0.0.0', 8080), blogger)
        http_server.serve_forever()
