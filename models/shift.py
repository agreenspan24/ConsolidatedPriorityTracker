from app import db, schema
from sqlalchemy import Table, Column
from models import volunteer, canvassgroup, location, user, note
from datetime import datetime, timedelta

# Object representing an individual event signup or shift. References the volunteer, canvass groups, etc.
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
    volunteer = db.relationship(volunteer.Volunteer, lazy='joined')
    shift_location = db.Column(db.Integer, db.ForeignKey(schema + '.location.locationid'), index=True)
    location = db.relationship(location.Location, lazy='joined')
    notes = db.relationship(note.Note, lazy='joined')
    canvass_group = db.Column(db.Integer, db.ForeignKey(schema + '.canvass_group.id'), index=True)
    group = db.relationship("CanvassGroup")
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)
    shift_flipped = db.Column(db.Boolean)
    claim = db.Column(db.Integer, db.ForeignKey(schema + '.users.id'), index=True)
    claim_user = db.relationship(user.User, lazy='joined')
    is_active = db.Column(db.Boolean)

    def __init__(self, eventtype, time, date, status, role, person, shift_location, last_user=None):

        self.eventtype = eventtype
        self.time = time
        self.date = date
        self.status = status
        self.o_status = status
        self.role = role
        self.flake = False
        self.person = person
        self.shift_location = shift_location
        self.call_pass = 0
        self.flake_pass = 0
        self.last_user = last_user
        self.last_update = datetime.now().time()
        self.shift_flipped = False
        self.is_active = True

    def flip(self, page, status, user):
        print('flip', page, status, user)
        if status == 'No Show':
            self.flake = True

        new_note = self.add_note(page, self.status + ' to ' + status, user)
        
        self.status = status

        self.shift_flipped = False

        return new_note


    def add_note(self, page, text, user):
        self.last_contact = datetime.now().time().strftime('%I:%M %p')

        five_min_ago = datetime.now() - timedelta(minutes=5)
        recent_note = next((x for x in self.notes if x.type == page and x.time > five_min_ago.time()), None)

        if recent_note:
            recent_note.time = datetime.now().time()
            recent_note.text = recent_note.text + '; ' + text
        else:
            new_note = note.Note(page, self.last_contact, text, self.id, user)
            db.session.add(new_note)

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
            'time': self.time.strftime('%I:%M %p'),
            'date': self.date.strftime('%Y-%m-%d'),
            'status': self.status,
            'o_status': self.o_status,
            'role': self.role,
            'flake': self.flake,
            'person': self.person,
            'volunteer': self.volunteer.serialize(),
            'location': self.location.serialize(),
            'call_pass': self.call_pass,
            'flake_pass': self.flake_pass,
            'notes': sorted(list(map(lambda x: x.serialize(), self.notes)), key=lambda n: n['time'], reverse=True),
            'volunteer': self.volunteer.serialize(),
            'location': self.location.serialize(),
            'claim': self.claim,
            'claim_user': (self.claim_user.serialize() if self.claim_user != None else None)
        }
