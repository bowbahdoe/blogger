import os
import flask
import typing
import markdown
import functools
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from gevent.wsgi import WSGIServer

DEBUG = True
app = flask.Flask(__name__)


BLOG_FOLDER = 'blog_posts'
BLOG_PATH = os.path.join(app.static_folder, BLOG_FOLDER)

@app.route('/blog_posts/<path:selection>')
@functools.lru_cache(2**10)
def post_view(selection):
    '''
    returns dynamically the html of the given blog page
    '''
    
    for absolute, relative in resource_paths():
        trim_length = len(BLOG_FOLDER) + 1
        if relative[trim_length:] == selection:
            return flask.jsonify(post_fetcher(absolute))

    return flask.jsonify(error=404, text='unable to find post'), 404

@app.route('/get_blog_routes')
@functools.lru_cache(2**8)
def get_blog_routes():
    '''
    returns a list of all the URIs for blog posts
    '''
    uris = [relative for absolute, relative in resource_paths()]
    return flask.jsonify(uris)
    
def resource_paths():
    '''
    returns a generator of tuples of the absolute path and relative path of
    every markdown resource
    '''
    for path, _, files in os.walk(BLOG_PATH):
        for name in files:
            absolute_path = os.path.join(path, name)
            relative_path = os.path.relpath(absolute_path,app.static_folder)
            yield absolute_path, relative_path

def create_dir():
    '''
    looks for the directory where we store blog posts, and if it
    doesnt exist creates it
    '''

    try:
        os.stat(BLOG_PATH)
    except:
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
        app.run(port=8080,host='0.0.0.0')
    else:
        http_server = WSGIServer(('0.0.0.0', 8080), app)
        http_server.serve_forever()