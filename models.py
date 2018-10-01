from app import app, db
from config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('postgresql+psycopg2://' + settings.get('sql_username') + ':' + settings.get('sql_pass') +  '@reporting.czrfudjhpfwo.us-east-2.rds.amazonaws.com:5432/mcc')

class SyncShift(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'syncshifts'
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

class Location(db.Model):
    __table_args__ = {'schema':'consolidated'}
    #__tablename__ = 'location'

    locationid = db.Column(db.Integer, primary_key=True)
    locationname = db.Column(db.String(50))
    region = db.Column(db.String(2))
    shifts = db.relationship('Shift', backref='location')

    def __init__(self, locationid, locationname, region):

        self.locationid = locationid
        self.locationname = locationname
        self.region = region

class User(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True)
    #fullname = db.Column('fullname', db.String(120))
    email = db.Column('email', db.String(120), unique=True)
    rank = db.Column('rank', db.String(120))
    region = db.Column('region', db.String(120))
    office = db.Column('office', db.String(120))
    openid = db.Column('openid', db.String(50))

class Volunteer(db.Model):
    __table_args__ = {'schema':'consolidated'}
    #__tablename__ = 'volunteer'

    #id = db.Column(db.Integer, primary_key=True)
    van_id = db.Column(db.Integer, primary_key=True)
    knocks = db.Column(db.Integer)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    phone_number = db.Column(db.String(120))
    cellphone = db.Column(db.String(120))
    shifts = db.relationship('Shift', backref='volunteer')

    def __init__(self, van_id, first_name, last_name, phone_number, cellphone, is_intern=False, knocks=0):
        
        self.van_id = van_id
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.cellphone = cellphone
        self.knocks = 0
        self.is_intern = is_intern

class Shift(db.Model):
    __table_args__ = {'schema':'consolidated'}
    #__tablename__ = 'shift'

    id = db.Column(db.Integer, primary_key=True)
    #event_shift_id = db.Column(db.Integer)
    eventtype = db.Column(db.String(120))
    time = db.Column(db.Time)
    date = db.Column(db.Date)
    status = db.Column(db.String(120))
    role = db.Column(db.String(120))
    knocks = db.Column(db.Integer)
    actual = db.Column(db.Integer)
    goal = db.Column(db.Integer)
    packets_given = db.Column(db.Integer)
    packet_names = db.Column(db.String(255))
    flake = db.Column(db.Boolean)
    flake_passed = db.Column(db.Integer)
    departure = db.Column(db.Time)
    last_contact = db.Column(db.Time)
    returned = db.Column(db.Boolean)
    notes = db.Column(db.String(255))
    person = db.Column(db.Integer, db.ForeignKey('consolidated.volunteer.van_id'))
    shift_location = db.Column(db.Integer, db.ForeignKey('consolidated.location.locationid'))

    def __init__(self, eventtype, time, date, status, role, person, shift_location):

        #self.event_signup_id = event_signup_id
        #self.event_shift_id = event_shift_id
        self.eventtype = eventtype
        self.time = time
        self.date = date
        self.status = status
        self.role = role
        self.actual = 0
        self.goal = 0
        self.packets_given = 0
        self.packet_names = ''
        self.flake = False
        self.flake_passes = 0
        self.departure = None
        self.last_contact = None
        self.returned = False
        self.notes = ''
        #self.event_id = event_id
        self.person = person
        self.shift_location = shift_location

    






