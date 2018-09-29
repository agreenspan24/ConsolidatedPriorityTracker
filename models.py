from app import app, db

class Volunteer(db.Model):

    #id = db.Column(db.Integer, primary_key=True)
    van_id = db.Column(db.Integer, primary_key=True)
    knocks = db.Column(db.Integer)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    phone_number = db.Column(db.String(120))
    is_intern = db.Column(db.Boolean)
    shifts = db.relationship('Shift', backref='volunteer')

    def __init__(self, van_id, first_name, last_name, phone_number, is_intern=False, knocks=0,):
        
        self.van_id = van_id
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.knocks = 0
        self.is_intern = is_intern

class Location(db.Model):

    #id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    region = db.Column(db.String(120))
    shifts = db.relationship('Shift', backref='location')

    def __init__(self, location_id, name, region):

        self.location_id = location_id
        self.name = name
        self.region = region

class Event(db.Model):
    
    #id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(120))
    date = db.Column(db.String(120))
    shifts = db.relationship('Shift', backref='event')
    
    def __init__(self, event_id, event_type, date):
        
        self.event_id = event_id
        self.event_type = event_type
        self.date = date

class Shift(db.Model):

    event_signup_id = db.Column(db.Integer, primary_key=True)
    event_shift_id = db.Column(db.Integer)
    time = db.Column(db.String(120))
    date = db.Column(db.String(120))
    status = db.Column(db.String(120))
    event_id = db.Column(db. Integer, db.ForeignKey('event.event_id'))
    person = db.Column(db.Integer, db.ForeignKey('volunteer.van_id'))
    shift_location = db.Column(db.Integer, db.ForeignKey('location.location_id'))

    def __init__(self, event_signup_id, event_shift_id, time, date, status, event_id, person, shift_location):

        self.event_signup_id = event_signup_id
        self.event_shift_id = event_shift_id
        self.time = time
        self.date = date
        self.status = status
        self.event_id = event_id
        self.person = person
        self.shift_location = shift_location
