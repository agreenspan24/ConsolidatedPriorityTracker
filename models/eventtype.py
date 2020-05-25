from app import db
from sqlalchemy import Table, Column

'''
Maps names of event types to their IDs in VAN, helping with sync
'''
class EventType(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'event_type'

    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100))