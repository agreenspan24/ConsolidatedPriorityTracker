from app import app, db

class KPH(db.Model):
    __table_args__ = {'schema':'consolidated'}

    position = db.Column(db.String(120))
    name = db.Column(db.String(120))
    goal = db.Column(db.Integer)
    has_returned = db.Column(db.Boolean)
    time_of_departure = db.Column(db.Date)
    phone_number = db.Column(db.String(50))
    next_check_in = db.Column(db.Date)
    final_amount = db.Column(db.Integer)

    packets = relationship('KPHPacket', secondary=post_keywords)
    check_ins = relationship('KPHCheckIn', secondary=post_keywords)

    def actual(self):
        return self.final_amount or sum(c.doors_knocked for c in self.check_ins)

class KPHPacket(db.Model):
    __table_args__ = {'schema':'consolidated'}

    packet_number = db.Column(db.String(120))

class KPHCheckIn(db.Model):
    __table_args__ = {'schema':'consolidated'}

    doors_knocked = db.Column(db.Integer)
    time = db.Column(db.Date)
    qualitative = db.Column(db.String(240))

class EventParticipant(db.Model):
    __table_args__ = {'schema':'consolidated'}

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

    passes = relationship('EventParticipantPasses', secondary=post_keywords)

    def same_day_confirmed(self):
        return any(passes.completed)
    
class EventParticipantPasses(db.Model):
    __table_args__ = {'schema':'consolidated'}

    note = db.Column(db.String(240))

    def completed(self):
        return "conf" in self.note

class EventParticipantStats:
    vol_confirmed
    vol_completed
    vol_declined
    vol_unflipped
    vol_flaked
    intern_completed
    intern_declined
