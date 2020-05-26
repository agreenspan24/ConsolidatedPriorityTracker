from app import db, schema
from sqlalchemy import Table, Column
from datetime import time

# Represents a note on a shift in the database. The type governs where it is shown: kph, flake, or sdc.
class Note(db.Model):
    __table_args__ = {'schema':schema}

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(7))
    time = db.Column(db.Time)
    text = db.Column(db.String(255))
    note_shift = db.Column(db.Integer, db.ForeignKey(schema + '.shift.id'))
    user_id = db.Column(db.Integer, db.ForeignKey(schema + '.users.id'))
    user_name = db.Column(db.String(2))
    user_color = db.Column(db.String(6))

    def __init__(self, type, time, text, note_shift, user):

        self.type = type
        self.time = time
        self.text = text
        self.note_shift = note_shift
        self.user_id = user.id
        self.user_name = user.claim_name()
        self.user_color = user.color

    def serialize(self):
        return {
            'type': self.type,
            'time': self.time.strftime('%I:%M %p'),
            'text': self.text,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_color': self.user_color
        }