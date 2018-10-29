
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_oidc import OpenIDConnect
import os
from sqlalchemy import create_engine

try:
    schema = os.environ['schema']
except:
    schema = 'consolidated'


os.environ['HEROKU_POSTGRESQL_AMBER_URL'] = 'postgres://udq8m08n6hjmcm:p3d9b763d9c7c20258eeca3568605c92a55d0aa84c8b6a6a63ded7a787f65e4a4@ec2-23-20-55-108.compute-1.amazonaws.com:5432/d2970fhsvk9kkq'
os.environ['secret_key'] = 'fasdjhkR#$@sdaf'

app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['HEROKU_POSTGRESQL_AMBER_URL'] 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['OIDC_CLIENT_SECRETS'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
app.config['OIDC_SCOPES'] = ['openid', 'email', 'profile']
app.config['OIDC_ID_TOKEN_COOKIE_SECURE'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1800
db = SQLAlchemy(app)
oid = OpenIDConnect()
app.secret_key = os.environ['secret_key']

engine = create_engine(os.environ['HEROKU_POSTGRESQL_AMBER_URL'])
'''engine = engine.execution_options(
    isolation_level="READ UNCOMMITTED"
)'''