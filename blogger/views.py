import os
import flask
import typing
import markdown
import functools
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from blogger import app


############################
# GENERATE BLOG POST URLS  #
############################

#############################################################################
# Global referenced from the api call that tells the frontend where to look #
#############################################################################
BLOG_ROUTES = []
BLOG_PATH = os.path.join(app.static_folder, 'blog_posts')

def generate_blog_routes() -> None:
    '''
    gives all of the markdown files under static/blog_posts a view
    under /blog_posts that represents their rendered HTML
    
    registers all of these paths under the app object
    '''

    #####################################################################
    # We expect the folder to exist, but if it doesnt we will create it #
    #####################################################################
    
    try:
        os.stat(BLOG_PATH)
    except:
        os.mkdir(BLOG_PATH)
    
    ########################################################################
    # We default the relative paths of the blog posts to be where they are #
    # located in terms of route                                            #
    ########################################################################
    
    REL_PATHS = []
    ABS_PATHS = []
    for path, _, files in os.walk(BLOG_PATH):
        for name in files:
            absolute_path = os.path.join(BLOG_PATH, name)
            relative_path = os.path.relpath(absolute_path,app.static_folder)
            ABS_PATHS.append(absolute_path)
            REL_PATHS.append(relative_path)
    
    #################################################
    # Assigns the paths of the blog posts to routes #
    #################################################
    for relative, absolute in zip(REL_PATHS, ABS_PATHS):
        register = app.route(os.path.join("/", relative), endpoint = relative)
        view = make_fetching_procedure(absolute)
        cached_view = functools.lru_cache(maxsize=None)(view)
        register(cached_view)
    
    #########################################################################
    # update the BLOG_ROUTES global to support telling the client where the #
    # posts are located                                                     #
    #########################################################################
    global BLOG_ROUTES
    BLOG_ROUTES = REL_PATHS[:]
    
def make_fetching_procedure(path) -> typing.Callable[[], str]:
    '''
    creates a procedure that will get the given markdown file out of static
    and serve the html representation
    
    path: the absolute path of the mardown file to be served
    
    (relies on flask's caching behaviour to get acceptable performance)
    '''
    def post_fetcher() -> str:
        with open(path, 'r') as markdown_file:
            return markdown.markdown(markdown_file.read())
    
    return post_fetcher

@app.route('/api/get_blog_routes')
def get_blog_routes():
    '''
    returns a list of all the contents of BLOG_ROUTES
    '''
    return flask.jsonify(BLOG_ROUTES)

########################################################################
# The routes we generate dont work unless we run setup, so we run that #
# on every import                                                      #
########################################################################
generate_blog_routes()
#generate_blog_routes() #BLERP ERROR
####################################################################
# We also want watching behaviour so the server doesnt need to be  #
# restarted on every change                                        #
#                                                                  #
# We make the implicit assumption of refresh for changes to posts; #
# there is no mechanism for a frontend client to detect a change   #
####################################################################
class ReloadFiles(FileSystemEventHandler):
    def on_any_event(self, event):
        print("should reload now")
_event_handler = ReloadFiles()
_observer = Observer()
_observer.schedule(_event_handler, BLOG_PATH, recursive=True)
_observer.start()