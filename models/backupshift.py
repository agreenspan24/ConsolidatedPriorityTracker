from app import db, schema
from sqlalchemy import Table, Column
from models import volunteer, backupgroup, location

# Represents the backup of a shift, pointed to its volunteer record and location
class BackupShift(db.Model):
    __table_args__ = {'schema':'backup'}
    __tablename__ = 'backup_shift'

    id = db.Column('id', db.Integer, primary_key=True)
    eventtype = db.Column('eventtype', db.String(120))
    date = db.Column(db.Date)
    time = db.Column('time', db.Time)
    role = db.Column(db.String(120))
    status = db.Column('status', db.String(120))
    shift_flipped = db.Column(db.Boolean)
    shift_location = db.Column(db.Integer, db.ForeignKey(schema + '.location.locationid'))
    location = db.relationship(location.Location, lazy='joined')
    person = db.Column(db.Integer, db.ForeignKey(schema + '.volunteer.id'))
    volunteer = db.relationship(volunteer.Volunteer, lazy='joined')
    canvass_group = db.Column(db.Integer, db.ForeignKey('backup.backup_group.id'))
    group = db.relationship("BackupGroup")

    def __init__(self, shift):
        self.eventtype = shift.eventtype
        self.date = shift.date
        self.time = shift.time
        self.role = shift.role
        self.status = shift.status
        self.shift_flipped = shift.shift_flipped
        self.shift_location = shift.shift_location
        self.person = shift.person