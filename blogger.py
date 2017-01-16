import os
import flask
import typing
import markdown
import functools
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


app = flask.Flask(__name__)

# BLOG_ROUTES is a List[{'uri': str, 'html': str}]
BLOG_ROUTES = []
BLOG_FOLDER = 'blog_posts'
BLOG_PATH = os.path.join(app.static_folder, BLOG_FOLDER)

def create_dir():
    '''
    looks for the directory where we store blog posts, and if it
    doesnt exist creates it
    '''
    try:
        os.stat(app.static_folder)
    except:
        os.mkdir(app.static_folder)

    try:
        os.stat(BLOG_PATH)
    except:
        os.mkdir(BLOG_PATH)

def populate_blog_routes():
    '''
    Adds all the routes for the static blog pages to BLOG_ROUTES
    '''
    BLOG_ROUTES[:] = []
    for path, _, files in os.walk(BLOG_PATH):
        for name in files:
            absolute_path = os.path.join(path, name)
            relative_path = os.path.relpath(absolute_path,app.static_folder)
            
            trim_length = len(BLOG_FOLDER) + 1
            BLOG_ROUTES.append({'uri': relative_path[trim_length:],
                                'html': post_fetcher(absolute_path)})

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
        initialize_blog()

def start_watcher():
    '''
    starts a watcher in the background that reloads markdown templates if
    a change is made
    '''
    event_handler = ReloadFiles()
    observer = Observer()
    observer.schedule(_event_handler, BLOG_PATH, recursive=True)
    observer.start()

def initialize_blog():
    create_dir()
    populate_blog_routes()
    post_view.cache_clear()

@app.route('/blog_posts/<path:selection>')
@functools.lru_cache(maxsize=2**6)
def post_view(selection):
    print(BLOG_ROUTES)
    for route in BLOG_ROUTES:
        if route['uri'] == selection:
            return flask.jsonify(route['html'])
    return flask.jsonify(error=404, text='unable to find post'), 404




@app.route('/get_blog_routes')
def get_blog_routes():
    '''
    returns a list of all the URIs for blog posts
    '''
    uris = [os.path.join(BLOG_FOLDER, route['uri']) for route in BLOG_ROUTES]
    return flask.jsonify(uris)

initialize_blog()

if __name__ == '__main__':
    start_watcher()
    app.run(port=8080,host='0.0.0.0')