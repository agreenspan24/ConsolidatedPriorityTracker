
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_oidc import OpenIDConnect
import os
from sqlalchemy import create_engine

try:
    schema = os.environ['schema']
except:
    schema = 'consolidated'

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['HEROKU_POSTGRESQL_AMBER_URL'] 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['OIDC_CLIENT_SECRETS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
app.config['OIDC_SCOPES'] = ['openid', 'email', 'profile']
app.config['OIDC_ID_TOKEN_COOKIE_SECURE'] = False
db = SQLAlchemy(app)
oid = OpenIDConnect()
engine = create_engine(os.environ['HEROKU_POSTGRESQL_AMBER_URL'])
app.secret_key = os.environ['secret_key']