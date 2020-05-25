from app import db, schema
from sqlalchemy import Table, Column
from models import note

class User(db.Model):
    __table_args__ = {'schema':schema}
    __tablename__ = 'users'

    id = db.Column('id', db.Integer, primary_key=True)
    fullname = db.Column('full_name', db.String(240))
    firstname = db.Column('first_name', db.String(120))
    lastname = db.Column('last_name', db.String(120))
    email = db.Column('email', db.String(120), index=True, unique=True)
    rank = db.Column('rank', db.String(120))
    region = db.Column('region', db.String(120))
    office = db.Column('office', db.String(120))
    openid = db.Column('openid', db.String(50))
    is_allowed = db.Column('is_allowed', db.Boolean)
    color = db.Column('color', db.String(6))
    notes = db.relationship(note.Note)

    def __init__(self, email, openid=None, rank=None, region=None, office=None, is_allowed=False, firstname=None, lastname=None):
        self.email = email
        self.openid = openid
        self.rank = rank
        self.region = region
        self.office = office
        self.is_allowed = is_allowed
        self.firstname = firstname
        self.lastname = lastname
        

    def serialize(self):
        return {
            'id': self.id,
            'fullname': self.fullname,
            'color': self.color,
            'claim_name': self.claim_name()
        }

    def claim_name(self):
        return (self.firstname[0]+ self.lastname[0]).upper() if (not self.firstname in [None, ''] and not self.lastname in [None, '']) else self.email[:2]
   