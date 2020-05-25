from app import db, schema
from sqlalchemy import Table, Column

'''
Represents the event location from VAN
'''
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