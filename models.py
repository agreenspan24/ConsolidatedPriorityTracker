from app import app, db, engine
from sqlalchemy import create_engine, Table, MetaData, Column, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from datetime import datetime, time, timedelta
from sqlalchemy.inspection import inspect
from sqlalchemy_views import CreateView, DropView
from dashboard_totals import DashboardTotal
import os

def create_view(view, definition):
    create_view = CreateView(view, definition)
    return create_view

def drop_view(view):
    drop_view = DropView(view)
    return drop_view

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

class Location(db.Model):
    __table_args__ = {'schema':'consolidated'}
    #__tablename__ = 'location'

    locationid = db.Column(db.Integer, primary_key=True)
    actual_location_name = db.Column(db.String(50))
    locationname = db.Column(db.String(50))
    region = db.Column(db.String(2))
    shifts = db.relationship('Shift', backref='location')

    def __init__(self, locationid, actual_location_name, locationname, region):

        self.locationid = locationid
        self.actual_location_name = actual_location_name
        self.locationname = locationname
        self.region = region

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

class User(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True)
    fullname = db.Column('full_name', db.String(240))
    firstname = db.Column('first_name', db.String(120))
    lastname = db.Column('last_name', db.String(120))
    email = db.Column('email', db.String(120), unique=True)
    rank = db.Column('rank', db.String(120))
    region = db.Column('region', db.String(120))
    office = db.Column('office', db.String(120))
    openid = db.Column('openid', db.String(50))
    is_allowed = db.Column('is_allowed', db.Boolean)

class ShiftStatus(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'shiftstatus'

    id = db.Column('statusid', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100))


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
    #next_shift = db.Column(db.Date)

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
        #self.next_shift = None

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

    def add_note(self, page, text):
        self.last_contact = datetime.now().time().strftime('%I:%M %p')
        note = Note(page, self.last_contact, text, self.person, self.id)

        db.session.add(note)

        return self.last_contact + ": " + text

    def add_pass(self):
        if self.call_pass == None:
            self.call_pass = 1
        else:
            self.call_pass += 1
        
        return self.call_pass

    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    def updated_by_other(self, page_load_time, user):
        return self.last_user != user.id and self.last_update != None and self.last_update > page_load_time

        
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

        if len(shift_ids) < 1:
            return abort(400, 'Group must have at least one canvasser')

        for id in shift_ids:
            shift = Shift.query.get(id)

            if not shift:
                return abort(400, 'Shift not found')

            if shift.canvass_group != None:
                return abort(400, 'Canvasser can only be in one group')
                
            self.canvass_shifts.append(shift)

        return self.canvass_shifts

    def check_in(self, check_in_amount):

        self.last_check_in = datetime.now().time()
        self.check_in_time = time(self.last_check_in.hour + 1, self.last_check_in.minute)
        self.check_ins += 1
        self.actual = int(check_in_amount)

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
            return_var = shift.add_note(page, text)

        return return_var

    def updated_by_other(self, page_load_time, user):
        return self.last_user != user.id and self.last_update != None and self.last_update > page_load_time


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
                if s.status in ["Scheduled", 'Confirmed', 'Same Day Confirmed']:
                    self.vol_unflipped += 1
                if s.status == "No Show":
                    self.vol_flaked += 1

        knocks = 0
        for g in groups:
            if g.is_returned:
                knocks += g.actual

        shifts = self.intern_completed + self.vol_completed
        self.kps = knocks / (shifts if shifts > 0 else 1)


class HeaderStats:
    def __init__(self, shifts, groups):
        time_now = datetime.now().time()

        self.overdue_check_ins = sum(1 for x in groups if x.check_in_time != None and x.check_in_time < time_now)
        self.flakes_not_chased = sum(1 for x in shifts if x.flake and x.status == 'No Show')
