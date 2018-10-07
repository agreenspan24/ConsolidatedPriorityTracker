from app import app, db
from config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, time, timedelta
from sqlalchemy.inspection import inspect

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

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

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
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)

    def __init__(self, van_id, first_name, last_name, phone_number, cellphone, is_intern=False, knocks=0):
        
        self.van_id = van_id
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.cellphone = cellphone
        self.knocks = 0
        self.is_intern = is_intern
        self.last_user = None
        self.last_update = None

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}


class Note(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(7))
    time = db.Column(db.Time)
    text = db.Column(db.String(255))
    volunteer = db.Column(db.Integer, db.ForeignKey('consolidated.volunteer.id'))
    note_shift = db.Column(db.Integer, db.ForeignKey('consolidated.shift.id'))

    def __init__(self, type, time, text, volunteer, note_shift):

        self.type = type
        self.time = time
        self.text = text
        self.volunteer = volunteer
        self.note_shift = note_shift

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}


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
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)

    def __init__(self, eventtype, time, date, status, role, person, shift_location):

        #self.event_signup_id = event_signup_id
        #self.event_shift_id = event_shift_id
        self.eventtype = eventtype
        self.time = time
        self.date = date
        self.status = status
        self.role = role
        self.flake = False
        self.last_contact = None
        #self.event_id = event_id
        self.person = person
        self.shift_location = shift_location
        self.call_pass = 0
        self.last_user = None
        self.last_update = None

    def flip(self, status):
        if self.status in ['Invited', 'Left Message'] and not status in ['Completed', 'Same Day Confirmed', 'In']:
            return

        elif status == 'No Show':
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

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}


class ShiftStats:
    def __init__(self, shifts, groups):
        self.vol_confirmed = 0
        self.vol_completed = 0
        self.vol_declined = 0
        self.vol_unflipped = 0
        self.vol_flaked = 0
        self.intern_completed = 0
        self.intern_declined = 0
        self.kps = 0

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
                if s.status == "No Show":
                    self.vol_flaked += 1

        knocks = 0
        for g in groups:
            if g.is_returned:
                knocks += g.actual
        shifts = self.intern_completed + self.vol_completed
        self.kps = knocks / (shifts if shifts > 0 else 1)

        
class CanvassGroup(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key = True)
    actual = db.Column(db.Integer)
    goal = db.Column(db.Integer)
    packets_given = db.Column(db.Integer)
    packet_names = db.Column(db.String(255))
    is_returned = db.Column(db.Boolean)
    departure = db.Column(db.Time)
    last_check_in = db.Column(db.Time)
    check_in_time = db.Column(db.Time)
    check_ins = db.Column(db.Integer)
    canvass_shifts = db.relationship('Shift', backref='group')
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)

    def __init__(self):
        self.actual = 0
        self.goal = 0
        self.packets_given = 0
        self.packet_names = ''
        self.is_returned = False
        self.departure = None
        self.last_contact = None
        self.check_in_time = None
        self.check_ins = 0
        self.last_user = None
        self.last_update = None


    def update_shifts(self, shift_ids):
        self.canvass_shifts = []
        return_var = ''

        for id in shift_ids:
            shift = Shift.query.get(id)

            if not shift:
                return abort(400, 'Shift not found')
                ','
            self.canvass_shifts.append(shift)

        return self.canvass_shifts

    def check_in(self, check_in_amount):

        self.last_check_in = datetime.now().time()
        self.check_in_time = time(self.last_check_in.hour + 1, self.last_check_in.minute)
        self.check_ins += 1
        self.actual += int(check_in_amount)

        return self

    def setOut(self):

        if self.departure == None:
            self.departure = datetime.now().time()
            self.last_check_in = datetime.now().time()
            self.check_in_time = time(self.last_check_in.hour + 1, self.last_check_in.minute)

            return self

        self.is_returned = not self.is_returned
        self.last_check_in = datetime.now().time()

        if self.is_returned:
            self.check_in_time = None
            for shift in self.canvass_shifts:
                shift.status = 'Completed'
        
        else:
            self.check_in_time = datetime.now() + timedelta(hours=1)
            for shift in self.canvass_shifts:
                shift.status = 'In'

        return self

    def add_note(self, page, text):
        return_var = ''
        for shift in self.canvass_shifts:
            return_var = shift.add_call_pass(page, text)

        return return_var

    

class DashboardTotal(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'dashboard_totals'

    id = db.Column('id', db.Integer, primary_key=True)
    region = db.Column('region', db.String(10))
    office = db.Column('office', db.String(50))
    canvass_total_scheduled = db.Column('canvass_total_scheduled', db.Integer)
    canvass_same_day_confirmed = db.Column('canvass_same_day_confirmed', db.Integer)
    canvass_completed = db.Column('canvass_completed', db.Integer)
    canvass_declined = db.Column('canvass_declined', db.Integer)
    canvass_flaked = db.Column('canvass_flaked', db.Integer)
    phone_total_scheduled = db.Column('phone_total_scheduled', db.Integer)
    phone_same_day_confirmed = db.Column('phone_same_day_confirmed', db.Integer)
    phone_completed = db.Column('phone_completed', db.Integer)
    phone_declined = db.Column('phone_declined', db.Integer)
    phone_flaked = db.Column('phone_flaked', db.Integer)
    flake_total = db.Column('flake_total', db.Integer)
    flake_attempts = db.Column('flake_attempts', db.Integer)
    flake_attempts_perc = db.Column('flake_attempts_perc', db.Integer)
    flake_rescheduled = db.Column('flake_rescheduled', db.Integer)
    flake_rescheduled_perc = db.Column('flake_rescheduled_perc', db.Integer)
    flake_chase_remaining = db.Column('flake_chase_remaining', db.Integer)
    flake_chase_remaining_perc = db.Column('flake_chase_remaining_perc', db.Integer)
    canvassers_all_day = db.Column('canvassers_all_day', db.Integer)
    actual_all_day = db.Column('actual_all_day', db.Integer)
    goal_all_day = db.Column('goal_all_day', db.Integer)
    packets_out_all_day = db.Column('packets_out_all_day', db.Integer)
    kps = db.Column('kps', db.Integer)
    canvassers_out_now = db.Column('canvassers_out_now', db.Integer)
    actual_out_now = db.Column('actual_out_now', db.Integer)
    goal_out_now = db.Column('goal_out_now', db.Integer)
    packets_out_now = db.Column('packets_out_now', db.Integer)
    kph = db.Column('kph', db.Integer)
    overdue_check_ins = db.Column('overdue_check_ins', db.Integer)
    





