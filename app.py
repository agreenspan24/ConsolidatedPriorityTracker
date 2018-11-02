
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_oidc import OpenIDConnect
import os

from sqlalchemy import create_engine
from flask_socketio import SocketIO
from flask_cache_buster import CacheBuster
from werkzeug.contrib.fixers import ProxyFix

try:
    schema = os.environ['schema']
except:
    schema = 'test'


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

# For additional debugging, add:
# logger=True, engineio_logger=True to SocketIO
socketio = SocketIO(app)

app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'] 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['OIDC_CLIENT_SECRETS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
app.config['OIDC_SCOPES'] = ['openid', 'email', 'profile']
app.config['OIDC_ID_TOKEN_COOKIE_SECURE'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1800
db = SQLAlchemy(app)
oid = OpenIDConnect()
app.secret_key = os.environ['secret_key']

cache_config = {
     'extensions': ['.js', '.css'],
     'hash_size': 10
}
cache_buster = CacheBuster(config=cache_config)
cache_buster.register_cache_buster(app)

if schema == 'test':
    app.config['SQLALCHEMY_ECHO'] = True

engine = create_engine(os.environ['DATABASE_URL'])
'''engine = engine.execution_options(
    isolation_level="READ UNCOMMITTED"
)'''