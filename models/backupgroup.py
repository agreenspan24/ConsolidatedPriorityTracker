from app import db
from sqlalchemy import Table, Column
from models import backupshift

# Represents a Canvass Group that has been backed up from a previous day
class BackupGroup(db.Model):
    __table_args__ = {'schema':'backup'}
    __tablename__ = 'backup_group'

    id = db.Column('id', db.Integer, primary_key=True)
    actual = db.Column('actual', db.Integer)
    goal = db.Column('goal', db.Integer)
    packet_names = db.Column('packet_names', db.String(255))
    is_returned = db.Column('is_returned', db.Boolean)
    canvass_shifts = db.relationship("BackupShift")

    def __init__(self, group):
        self.actual = group.actual
        self.goal = group.goal
        self.packet_names = group.packet_names
        self.is_returned = group.is_returned