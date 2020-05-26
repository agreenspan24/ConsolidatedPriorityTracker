from app import db, schema
from sqlalchemy import Table, Column
from utility import van_obfuscate

# This represents an outside volunteer, corresponding to their VAN record with the VAN id.
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
    next_shift_time = db.Column(db.Time)
    next_shift_confirmed = db.Column(db.Boolean)
    has_pitched_today = db.Column(db.Boolean)
    extra_shifts_sched = db.Column(db.Integer)

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
        self.next_shift_time = None
        self.next_shift_confirmed = False
        self.has_pitched_today = False
        self.extra_shifts_sched = None

    def serialize(self):
        return {
            'id': self.id,
            'van_id': self.van_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'cellphone': self.cellphone,
            'has_pitched_today': self.has_pitched_today,
            'extra_shifts_sched': self.extra_shifts_sched, 
            'code': van_obfuscate(self.van_id)
        }

    def updated_by_other(self, page_load_time, user):
        return self.last_user != user.id and self.last_update != None and self.last_update > page_load_time
