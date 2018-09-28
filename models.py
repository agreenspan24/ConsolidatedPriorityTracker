from app import app, db

class KPH(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.String(120))
    name = db.Column(db.String(120))
    goal = db.Column(db.Integer)
    has_returned = db.Column(db.Boolean)
    time_of_departure = db.Column(db.Date)
    phone_number = db.Column(db.String(50))
    next_check_in = db.Column(db.Date)
    final_amount = db.Column(db.Integer)

    """ packets = db.relationship('KPHPacket', backref=post_keywords)
    check_ins = db.relationship('KPHCheckIn', secondary=post_keywords)"""

    def __init__(self, position, name, goal, has_returned, time_of_departure, phone_number, next_check_in, final_amount, packets, check_ins):

        self.position = position
        self.name = name
        self.goal = goal
        self.has_returned = has_returned
        self.time_of_departure = time_of_departure
        self.phone_number = phone_number
        self.next_check_in = next_check_in
        self.final_amount = final_amount
        self.packets = packets
        self.check_ins = check_ins



    def actual(self):
        return self.final_amount or sum(c.doors_knocked for c in self.check_ins)

class KPHPacket(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key=True)
    packet_number = db.Column(db.String(120))

    def __init__ (self, packet_number):

        self.packet_number = packet_number

class KPHCheckIn(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key=True)
    doors_knocked = db.Column(db.Integer)
    time = db.Column(db.Date)
    qualitative = db.Column(db.String(240))

    def __init__(self, doors_knocked, time, qualitative):

        self.doors_knocked = doors_knocked
        self.time = time
        self.qualitative = qualitative

class EventParticipant(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key=True)
    van_id = db.Column(db.BigInteger)
    name = db.Column(db.String(120))
    phone_number = db.Column(db.String(50))
    cell_number = db.Column(db.String(50))
    location = db.Column(db.String(120))
    time = db.Column(db.String(120))
    role = db.Column(db.String(50))
    event = db.Column(db.String(120))
    status = db.Column(db.String(50))
    same_day_status = db.Column(db.String(50))
    flake_result = db.Column(db.String(50))

    #passes = relationship('EventParticipantPasses', secondary=post_keywords)

    def __init__(self, van_id, name, phone_number, cell_number, location, time, role, event, status, same_day_status, flake_result, passes):

        self.van_id = van_id
        self.name = name
        self.phone_number = phone_number
        self.cell_number = cell_number
        self.location = location
        self.time = time
        self.role = role
        self.event = event
        self.status = status
        self.same_day_status = same_day_status
        self.flake_result = flake_result
        self.passes = passes

    def same_day_confirmed(self):
        return any(self.passes.completed)
    
class EventParticipantPasses(db.Model):
    __table_args__ = {'schema':'consolidated'}

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(240))

    def __init__(self, note):
        self.note = note

    def confirmed(self):
        return "conf" in self.note


class EventParticipantStats:
    vol_confirmed
    vol_completed
    vol_declined
    vol_unflipped
    vol_flaked
    intern_completed
    intern_declined

    def __init__(self, confirms):
        self.vol_confirmed = 0
        self.vol_completed = 0
        self.vol_declined = 0
        self.vol_unflipped = 0
        self.vol_flaked = 0
        self.intern_completed = 0
        self.intern_declined = 0

        for c in confirms:
            if c.event == "Volunteer DVC":
                if c.same_day_confirmed():
                    self.vol_confirmed += 1
                if c.same_day_status == "Completed":
                    self.vol_completed += 1
                if c.same_day_status == "Declined":
                    self.vol_declined += 1
                if c.same_day_status is None or c.same_day_status = '':
                    self.vol_unflipped += 1
                if c.same_day_status == "Flaked":
                    self.vol_flaked += 1
            if c.event == "Intern DVC":
                if c.same_day_status == "Completed":
                    self.intern_completed += 1
                if c.same_day_status == "Declined":
                    self.intern_declined += 1
