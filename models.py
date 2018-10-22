from app import app, db, engine
from sqlalchemy import create_engine, Table, MetaData, Column, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
from datetime import datetime, time, timedelta
from sqlalchemy.inspection import inspect
from sqlalchemy_views import CreateView, DropView
from flask import abort
import os

schema = os.environ['schema']
#schema = 'consolidated'

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
    __table_args__ = {'schema':schema}
    #__tablename__ = 'location'

    locationid = db.Column(db.Integer, primary_key=True)
    actual_location_name = db.Column(db.String(50), index=True)
    locationname = db.Column(db.String(50), index=True)
    region = db.Column(db.String(2), index=True)

    def __init__(self, locationid, actual_location_name, locationname, region):

        self.locationid = locationid
        self.actual_location_name = actual_location_name
        self.locationname = locationname
        self.region = region

    def serialize(self):
        return {
            'locationid': self.locationid,
            'actual_location_name': self.actual_location_name,
            'locationname': self.locationname,
            'region': self.region
        }

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

    def __init__(self, email, openid):
        self.email = email
        self.openid = openid

    def serialize(self):
        return {
            'id': self.id,
            'fullname': self.fullname,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'email': self.email,
            'rank': self.rank,
            'region': self.region,
            'office': self.office,
            'color': self.color
        }

    def claim_name(self):
        return (self.firstname[0]+ self.lastname[0]).upper() if (not self.firstname in [None, ''] and not self.lastname in [None, '']) else self.email[:2]

class ShiftStatus(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'shiftstatus'

    id = db.Column('statusid', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100))

class EventType(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'event_type'

    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100))


class Volunteer(db.Model):
    __table_args__ = {'schema':schema}

    id = db.Column(db.Integer, primary_key=True)
    van_id = db.Column(db.Integer, index=True)
    knocks = db.Column(db.Integer)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    phone_number = db.Column(db.String(120))
    cellphone = db.Column(db.String(120))
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)
    next_shift = db.Column(db.Date)
    next_shift_confirmed = db.Column(db.Boolean)

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
        self.next_shift = None
        self.next_shift_confirmed = False

    def serialize(self):
        return {
            'id': self.id,
            'van_id': self.van_id,
            'knocks': self.knocks,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'cellphone': self.cellphone,
            'last_user': self.last_user,
            'last_update': self.last_update
        }

    def updated_by_other(self, page_load_time, user):
        return self.last_user != user.id and self.last_update != None and self.last_update > page_load_time


class Note(db.Model):
    __table_args__ = {'schema':schema}

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(7))
    time = db.Column(db.Time)
    text = db.Column(db.String(255))
    note_shift = db.Column(db.Integer, db.ForeignKey(schema + '.shift.id'))

    def __init__(self, type, time, text, note_shift):

        self.type = type
        self.time = time
        self.text = text
        self.note_shift = note_shift

    def serialize(self):
        return {
            'type': self.type,
            'time': self.time,
            'text': self.text
        }

        
class CanvassGroup(db.Model):
    __table_args__ = {'schema':schema}

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
    canvass_shifts = db.relationship('Shift', lazy='joined')
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)
    claim = db.Column(db.Integer, db.ForeignKey(schema + '.users.id'))
    claim_user = db.relationship(User, lazy='joined')
    is_active = db.Column(db.Boolean)

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
        self.claim = None

        self.is_active = True

    def update_shifts(self, shift_ids):
        old_shifts = self.canvass_shifts
        self.canvass_shifts = []

        if len(shift_ids) < 1:
            self.canvass_shifts = old_shifts
            return abort(400, 'Group must have at least one canvasser')

        for id in shift_ids:
            shift = Shift.query.get(id)

            if not shift or shift.is_active == False:
                self.canvass_shifts = old_shifts
                return abort(400, 'Shift not found')

            if shift.canvass_group != None and shift.group.is_active:
                self.canvass_shifts = old_shifts
                return abort(400, 'Canvasser can only be in one group')
                
            self.canvass_shifts.append(shift)

        return self.canvass_shifts

    def check_in(self, check_in_amount):

        self.last_check_in = datetime.now().time()
        self.check_in_time = datetime.now() + timedelta(hours=1)
        self.check_ins += 1
        self.actual = int(check_in_amount)

        return self

    def change_departure(self, departure_time_string):
        self.departure = departure_time_string.time()

        if self.check_ins == 0:
            self.last_check_in = self.departure
            self.check_in_time = departure_time_string + timedelta(minutes=45)

        return self
            
    def setOut(self):

        if self.departure == None:
            self.departure = datetime.now().time()
            self.last_check_in = datetime.now().time()
            self.check_in_time = datetime.now() + timedelta(minutes=45)

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

    def serialize(self):
        return {
            'id': self.id,
            'actual': self.actual,
            'goal': self.goal,
            'packets_given': self.packets_given,
            'packet_names': self.packet_names,
            'is_returned': self.is_returned,
            'departure': self.departure,
            'last_contact': self.last_contact,
            'check_in_time': self.check_in_time,
            'check_ins': self.check_ins,
            'last_user': self.last_user,
            'last_update': self.last_update,
            'canvass_shifts': list(map(lambda x: x.serialize(), self.canvass_shifts))
        }


class Shift(db.Model):
    __table_args__ = {'schema':schema}

    id = db.Column(db.Integer, primary_key=True)
    eventtype = db.Column(db.String(120), index=True)
    time = db.Column(db.Time, index=True)
    date = db.Column(db.Date, index=True)
    status = db.Column(db.String(120))
    o_status = db.Column(db.String(120), index=True)
    role = db.Column(db.String(120), index=True)
    knocks = db.Column(db.Integer)
    flake = db.Column(db.Boolean)
    call_pass = db.Column(db.Integer)
    flake_pass = db.Column(db.Integer)
    person = db.Column(db.Integer, db.ForeignKey(schema + '.volunteer.id'), index=True)
    volunteer = db.relationship(Volunteer, lazy='joined')
    shift_location = db.Column(db.Integer, db.ForeignKey(schema + '.location.locationid'), index=True)
    location = db.relationship(Location, lazy='joined')
    notes = db.relationship(Note, lazy='joined')
    canvass_group = db.Column(db.Integer, db.ForeignKey(schema + '.canvass_group.id'), index=True)
    group = db.relationship(CanvassGroup, lazy='joined')
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)
    shift_flipped = db.Column(db.Boolean)
    claim = db.Column(db.Integer, db.ForeignKey(schema + '.users.id'), index=True)
    claim_user = db.relationship(User, lazy='joined')
    is_active = db.Column(db.Boolean)

    def __init__(self, eventtype, time, date, status, role, person, shift_location):

        self.eventtype = eventtype
        self.time = time
        self.date = date
        self.status = status
        self.o_status = status
        self.role = role
        self.flake = False
        self.last_contact = None
        self.person = person
        self.shift_location = shift_location
        self.call_pass = 0
        self.flake_pass = 0
        self.last_user = None
        self.last_update = None
        self.shift_flipped = False
        self.is_active = True

    def flip(self, page, status):
        if status == 'No Show':
            self.flake = True

        note = self.add_note(page, self.status + ' to ' + status)
        
        self.status = status

        self.shift_flipped = False

        return note


    def add_note(self, page, text):
        self.last_contact = datetime.now().time().strftime('%I:%M %p')

        five_min_ago = datetime.now() - timedelta(minutes=5)
        recent_note = next((x for x in self.notes if x.type == page and x.time > five_min_ago.time()), None)

        if recent_note:
            recent_note.time = datetime.now().time()
            recent_note.text = recent_note.text + '; ' + text
        else:
            note = Note(page, self.last_contact, text, self.id)
            db.session.add(note)

        return self.last_contact + ": " + text

    def add_pass(self, page):
        if page == 'flake':
            if self.flake_pass == None:
                self.flake_pass = 1
            else:
                self.flake_pass += 1
            return self.flake_pass

        if page == 'sdc':
            if self.call_pass == None:
                self.call_pass = 1
            else:
                self.call_pass += 1
            return self.call_pass

    def updated_by_other(self, page_load_time, user):
        return self.last_user != user.id and self.last_update != None and self.last_update > page_load_time

    def serialize(self):
        return {
            'id': self.id,
            'eventtype': self.eventtype,
            'time': self.time,
            'date': self.date,
            'status': self.status,
            'role': self.role,
            'flake': self.flake,
            'last_contact': self.last_contact,
            'person': self.person,
            'volunteer': self.volunteer.serialize(),
            'shift_location': self.shift_location.serialize(),
            'call_pass': self.call_pass,
            'last_user': self.last_user,
            'last_update': self.last_update,
            'notes': list(map(lambda x: x.serialize(), self.notes)),
            'volunteer': self.volunteer.serialize(),
            'location': self.location.serialize()
        }


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
        self.actual = 0
        self.goal = 0
        self.percent_to_goal = 0.00
        self.packets_out = 0
        self.canvassers_out = 0

        for s in shifts:
            if s.eventtype == "Intern DVC":
                if s.status in ["Completed", "In"]:
                    self.intern_completed += 1
                if s.status == "Declined":
                    self.intern_declined += 1
            elif s.eventtype == "Volunteer DVC" and s.role == "Canvassing":
                if s.status == "Same Day Confirmed":
                    self.vol_confirmed += 1
                if s.status in ["Completed", "In"]:
                    self.vol_completed += 1
                if s.status == "Declined":
                    self.vol_declined += 1
                if s.status in ["Scheduled", 'Confirmed', 'Same Day Confirmed', 'Sched-Web']:
                    self.vol_unflipped += 1
                if s.status == "No Show":
                    self.vol_flaked += 1
            if s.status == 'In' and s.role = 'Canvassing':
                self.canvassers_out += 1


        knocks = 0
        for g in groups:
            if g.is_returned:
                knocks += g.actual
            else:
                self.packets_out += g.packets_given
            self.actual += g.actual
            self.goal += g.goal

        shifts = self.intern_completed + self.vol_completed
        self.kps = knocks / (shifts if shifts > 0 else 1)

        self.percent_to_goal = self.actual / (self.goal if self.goal > 0 else 1)


class HeaderStats:
    def __init__(self, shifts, groups):
        time_now = datetime.now()
        terminal_status = ['Resched', 'No Show', 'Completed', 'Declined']

        self.unflipped_shifts = sum(1 for x in shifts if x.status != 'In' and x.time < time_now.timedelta(minutes=20).time() and x.status not in terminal_status)
        self.overdue_check_ins = sum(1 for x in groups if not x.is_returned and x.check_in_time != None and x.check_in_time < time_now.time())
        self.flakes_not_chased = sum(1 for x in shifts if x.flake and x.status == 'No Show' and x.flake_pass < 1)


class BackupGroup(db.Model):
    __table_args__ = {'schema':'backup'}
    __tablename__ = 'backup_group'

    id = db.Column('id', db.Integer, primary_key=True)
    actual = db.Column('actual', db.Integer)
    goal = db.Column('goal', db.Integer)
    packet_names = db.Column('packet_names', db.String(255))
    is_returned = db.Column('is_returned', db.Boolean)
    canvass_shifts = db.relationship('BackupShift', lazy='joined')

    def __init__(self, group):
        self.actual = group.actual
        self.goal = group.goal
        self.packet_names = group.packet_names
        self.is_returned = group.is_returned


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
    location = db.relationship(Location, lazy='joined')
    person = db.Column(db.Integer, db.ForeignKey(schema + '.volunteer.id'))
    volunteer = db.relationship(Volunteer, lazy='joined')
    canvass_group = db.Column(db.Integer, db.ForeignKey('backup.backup_group.id'))
    group = db.relationship(BackupGroup, lazy='joined')

    def __init__(self, shift):
        self.eventtype = shift.eventtype
        self.date = shift.date
        self.time = shift.time
        self.role = shift.role
        self.status = shift.status
        self.shift_flipped = shift.shift_flipped
        self.shift_location = shift.shift_location
        self.person = shift.person