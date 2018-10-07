from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_oidc import OpenIDConnect
import os
from flask_oidc import OpenIDConnect

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://' + os.environ['sql_username'] + ':' + os.environ['sql_pass'] +  '@' + os.environ['server']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['OIDC_CLIENT_SECRETS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
app.config['OIDC_SCOPES'] = ['openid', 'email', 'profile']
app.config['OIDC_ID_TOKEN_COOKIE_SECURE'] = False
db = SQLAlchemy(app)
oid = OpenIDConnect()
app.secret_key = os.environ['secret_key']
