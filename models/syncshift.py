from app import db
from sqlalchemy import Table, Column

# This is the table that covers direct VAN imports from Event Participant List or Report. 
# Export must include these fields. Should be completely independent from rest of app.
class SyncShift(db.Model):
    __table_args__ = {'schema':'sync'}
    __tablename__ = 'shifts'

    id = db.Column('sync_id', db.Integer, primary_key=True)
    vanid = db.Column('vanid', db.Integer)
    eventtype = db.Column('eventtype', db.String(50))
    eventname = db.Column('eventname', db.String(50))
    startdate = db.Column('startdate', db.Date)
    starttime = db.Column('starttime', db.Time)
    locationname = db.Column('locationname', db.String(50))
    locationid = db.Column('locationid', db.Integer)
    role = db.Column('role', db.String(50))
    status = db.Column('status', db.String(50))
    firstname = db.Column('firstname', db.String(50))
    lastname = db.Column('lastname', db.String(50))
    phone = db.Column('phone', db.String(10))
    mobilephone = db.Column('mobilephone', db.String(10))

    def serialize(self): 
        return {
            'vanid': self.vanid,
            'eventtype': self.eventtype,
            'startdate': self.startdate.strftime('%m/%d'),
            'starttime': self.starttime.strftime('%I:%M %p'),
            'locationname': self.locationname,
            'role': self.role,
            'status': self.status,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'phone': self.phone,
            'mobilephone': self.mobilephone
        }