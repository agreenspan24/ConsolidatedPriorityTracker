from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import settings



app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://' + settings.get('sql_username') + ':' + settings.get('sql_pass') +  '@http://127.0.0.1:64201/mcc'
app.config['SQLALCHEMY_ECHO'] = False
db = SQLAlchemy(app)
app.secret_key = settings.get('secret_key')