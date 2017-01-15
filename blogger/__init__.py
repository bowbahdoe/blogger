import flask

##########################
# Setup main application #
##########################
app = flask.Flask(__name__)
app.config.from_pyfile('config.py')

###########################################
# Import the views so they are registered #
###########################################
import blogger.views