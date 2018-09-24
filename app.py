from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import settings



app = Flask(__name__)
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://' + settings.get('sql_username') + ':' + settings.get('sql_pass') +  '@localhost:8889/consolidated'
app.config['SQLALCHEMY_ECHO'] = False
db = SQLAlchemy(app)
app.secret_key = settings.get('secret_key')