from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_oidc import OpenIDConnect
from sqlalchemy import create_engine
import os

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://zmteqmujvkfnmq:8dce67c5ae02028c174df35be856535c90a9593280ab43edceadf25f3f76f97a@ec2-54-83-204-230.compute-1.amazonaws.com:5432/de8kcah93s00d9'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['OIDC_CLIENT_SECRETS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
app.config['OIDC_SCOPES'] = ['openid', 'email', 'profile']
app.config['OIDC_ID_TOKEN_COOKIE_SECURE'] = False
db = SQLAlchemy(app)
oid = OpenIDConnect()
engine = create_engine('postgresql+psycopg2://zmteqmujvkfnmq:8dce67c5ae02028c174df35be856535c90a9593280ab43edceadf25f3f76f97a@ec2-54-83-204-230.compute-1.amazonaws.com:5432/de8kcah93s00d9')
app.secret_key = 'fasdjhkR#$@sdaf'
