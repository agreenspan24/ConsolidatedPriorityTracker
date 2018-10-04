from app import app, db
from config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

engine = create_engine('postgresql+psycopg2://' + settings.get('sql_username') + ':' + settings.get('sql_pass') +  '@' + settings.get('server'))

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

    id = db.Column(db.Integer, primary_key=True)
    van_id = db.Column(db.Integer)
    knocks = db.Column(db.Integer)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    phone_number = db.Column(db.String(120))
    cellphone = db.Column(db.String(120))
    shifts = db.relationship('Shift', backref='volunteer')
    notes = db.relationship('Note', backref='note')

    def __init__(self, van_id, first_name, last_name, phone_number, cellphone, is_intern=False, knocks=0):
        
        self.van_id = van_id
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.cellphone = cellphone
        self.knocks = 0
        self.is_intern = is_intern


class Note(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(7))
    time = db.Column(db.Time)
    text = db.Column(db.String(255))
    volunteer = db.Column(db.Integer, db.ForeignKey('consolidated.volunteer.id'))
    note_shift = db.Column(db.Integer, db.ForeignKey('consolidated.shift.id'))

    def __init__(self, type, time, text, volunteer, note_shift):

        self.type
        self.time = time
        self.text = text
        self.volunteer = volunteer
        self.note_shift = note_shift


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
    flake = db.Column(db.Boolean)
    call_pass = db.Column(db.Integer)
    person = db.Column(db.Integer, db.ForeignKey('consolidated.volunteer.id'))
    shift_location = db.Column(db.Integer, db.ForeignKey('consolidated.location.locationid'))
    notes = db.relationship('Note', backref='shift')
    canvass_group = db.Column(db.Integer, db.ForeignKey('consolidated.canvass_group.id'))

    def __init__(self, eventtype, time, date, status, role, person, shift_location):

        #self.event_signup_id = event_signup_id
        #self.event_shift_id = event_shift_id
        self.eventtype = eventtype
        self.time = time
        self.date = date
        self.status = status
        self.role = role
        #self.event_id = event_id
        self.person = person
        self.shift_location = shift_location
        self.call_pass = 0

    def flip(self, status):
        
        if self.flake and status == 'Completed' or status == 'Same Day Confirmed':
            self.flake = False
        
        if status == 'Flake':
            self.flake = True

        self.status = status

    def add_call_pass(self, page, text):
        if self.call_pass == None:
            self.call_pass = 1
        else:
            self.call_pass += 1

        self.last_contact = datetime.now().time().strftime('%I:%M %p')
        note = Note(page, self.last_contact, text, self.person, self.id)

        db.session.add(note)

        return self.last_contact + ": " + text

    

    #TODO - CREATE NEW TABLE FOR SPECIFICALLY FOR KPH?

class ShiftStats:
    def __init__(self, shifts):
        self.vol_confirmed = 0
        self.vol_completed = 0
        self.vol_declined = 0
        self.vol_unflipped = 0
        self.vol_flaked = 0
        self.intern_completed = 0
        self.intern_declined = 0

        for s in shifts:
            if s.eventtype == "Intern DVC":
                if s.status == "Completed":
                    self.intern_completed += 1
                if s.status == "Declined":
                    self.intern_declined += 1
            else:
                if s.status == "Same Day Confirmed":
                    self.vol_confirmed += 1
                if s.status == "Completed":
                    self.vol_completed += 1
                if s.status == "Declined":
                    self.vol_declined += 1
                if s.status == "Scheduled":
                    self.vol_unflipped += 1
                if s.flake:
                    self.vol_flaked += 1
    
class CanvassGroup(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key = True)
    actual = db.Column(db.Integer)
    goal = db.Column(db.Integer)
    packets_given = db.Column(db.Integer)
    packet_names = db.Column(db.String(255))
    returned = db.Column(db.Boolean)
    departure = db.Column(db.Time)
    last_check_in = db.Column(db.Time)
    check_in_time = db.Column(db.Time)
    check_ins = db.Column(db.Integer)
    canvass_shifts = db.relationship('Shift', backref='group')

    def __init__(self):

        self.actual = 0
        self.goal = 0
        self.packets_given = 0
        self.packet_names = ''
        self.returned = False
        self.departure = "Hasn't left"
        self.last_contact = "Never"
        self.check_in_time = "Nothing Yet"
        self.check_ins = 0
        self.canvass_shifts = shifts

    def add_shifts(self, shifts):
    
        for shift in shifts:
            self.canvass_shifts.append(shift)

    def check_in(self):
        if self.departure == "Hasn't left":
            self.departure = datetime.now().time()
            self.check_in_time = self.departure.timedelta(hours=1)

        else:
            self.last_check_in = datetime.now().time()
            self.check_in_time = self.last_check_in.timedelta(hours=1)
            self.check_ins += 1

        return self

    def returned(self):

        self.returned = True

        for shift in self.canvass_shifts:
            shift.status = 'Completed'

    def add_note(self, page, text):
        self.canvass_shifts[0].add_call_pass(page, text)

    






