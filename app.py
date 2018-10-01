from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import settings
import os
from flask_oidc import OpenIDConnect



app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://' + settings.get('sql_username') + ':' + settings.get('sql_pass') +  '@reporting.czrfudjhpfwo.us-east-2.rds.amazonaws.com:5432/mcc'
app.config['SQLALCHEMY_ECHO'] = False
app.config['OIDC_CLIENT_SECRETS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
app.config['OIDC_SCOPES'] = ['openid', 'email', 'profile']
app.config['OIDC_ID_TOKEN_COOKIE_SECURE'] = False
db = SQLAlchemy(app)
app.secret_key = settings.get('secret_key')

oid = OpenIDConnect(app)

