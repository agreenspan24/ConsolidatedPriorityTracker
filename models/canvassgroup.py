from app import db, schema
from sqlalchemy import Table, Column
from models import shift, user
from datetime import datetime, timedelta

'''
Represents a group of shifts canvassing, including doors knocked and check-in information
'''  
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
    canvass_shifts = db.relationship(shift.Shift)
    last_user = db.Column(db.Integer)
    last_update = db.Column(db.Time)
    claim = db.Column(db.Integer, db.ForeignKey(schema + '.users.id'))
    claim_user = db.relationship(user.User, lazy='joined')
    is_active = db.Column(db.Boolean)

    def __init__(self, last_user=None):
        self.actual = 0
        self.goal = 0
        self.packets_given = 0
        self.packet_names = ''
        self.is_returned = False
        self.departure = None
        self.last_contact = None
        self.check_in_time = None
        self.check_ins = 0
        self.last_user = last_user
        self.last_update = datetime.now().time()
        self.claim = None

        self.is_active = True

    def update_shifts(self, shift_ids, user):
        old_shifts = self.canvass_shifts
        self.canvass_shifts = []

        if len(shift_ids) < 1:
            self.canvass_shifts = old_shifts
            return 'Group must have at least one canvasser'

        for id in shift_ids:
            s = shift.Shift.query.get(id)

            if not s or s.is_active == False:
                self.canvass_shifts = old_shifts
                return 'Shift not found'

            if s.canvass_group != None and s.group.is_active:
                self.canvass_shifts = old_shifts
                return 'Canvasser can only be in one group'

            if not s.status in ['In', 'Same Day Confirmed']:
                self.canvass_shifts = old_shifts
                return 'Canvassers must have status "In" or "Same Day Confirmed"'

            if s.status == 'Same Day Confirmed':
                s.flip('kph', 'In', user)
                
            self.canvass_shifts.append(s)

        return self.canvass_shifts

    def check_in(self, check_in_amount):

        self.actual = int(check_in_amount)

        if not self.is_returned:
            self.last_check_in = datetime.now().time()
            self.check_in_time = datetime.now() + timedelta(hours=1)
            self.check_ins += 1

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
            for s in self.canvass_shifts:
                s.status = 'Completed'
        
        else:
            self.check_in_time = datetime.now() + timedelta(hours=1)
            for s in self.canvass_shifts:
                s.status = 'In'

        return self

    def add_note(self, page, text, user):
        return_var = ''
        for s in self.canvass_shifts:
            return_var = s.add_note(page, text, user)

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
            'departure': (self.departure.strftime('%I:%M %p') if self.departure else None),
            'last_check_in': (self.last_check_in.strftime('%I:%M %p') if self.last_check_in else None),
            'check_in_time': (self.check_in_time.strftime('%I:%M %p') if self.check_in_time else None),
            'check_ins': self.check_ins,
            'canvass_shifts': list(map(lambda x: x.serialize(), self.canvass_shifts))
        }

