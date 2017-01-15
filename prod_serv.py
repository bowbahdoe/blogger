from gevent.wsgi import WSGIServer
from blogger import app

http_server = WSGIServer(('0.0.0.0', 8081), app)
http_server.serve_forever()