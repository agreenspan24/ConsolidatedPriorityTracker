from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import settings
from models import *



app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://' + settings.get('sql_username') + ':' + settings.get('sql_pass') +  '@reporting.czrfudjhpfwo.us-east-2.rds.amazonaws.com:5432/mcc'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = settings.get('secret_key')