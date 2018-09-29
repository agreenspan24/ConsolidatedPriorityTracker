from datetime import datetime
import requests
import simplejson
from requests.auth import HTTPBasicAuth

from config import settings
from models import *


class CPTVANAPI():

    def __init__(self, settings):

        self.settings = settings
        self.client = requests.Session()
        self.client.auth = (settings.get('api_key'), settings.get('api_pass'))
        self.regions = settings.get('regions')
        self.event_types = settings.get('event_types')
        self.event_status = settings.get('event_status')

    def get_event_type(self):
        """returns type ids containing plain text event name eg. 'canvassing', 'vol recruitment' located in settings"""
        types = self.client.get('https://api.securevan.com/v4/events/types').json()
        type_ids = {}
        for type in types:
            for e_type in self.event_types: 
                if e_type == type.get('name'):
                    type_ids[type.get('name')] = type.get('eventTypeId')

        return type_ids

    def get_event_ids(self):
        """gets all event ids associated with vol type ids and stores along with date"""
        event_type_ids = self.get_event_type()
        event_ids = {}
        for name, id in event_type_ids.items():
            events = self.client.get('https://api.securevan.com/v4/events?eventTypeIds={}&$top=50'.format(id)).json()
            more_pages = True

            while more_pages:
                for event in events.get('items'):
                    event_ids[event.get('eventId')] = [name, event.get('startDate')[0:10]]
                    new_event = Event(event.get('eventId'), name, event.get('startDate')[0:10])
                    db.session.add(new_event)

                if events.get('nextPageLink') == None:
                    more_pages = False
                else:
                    events = self.client.get(events.get('nextPageLink')).json()
        db.session.commit()     
        return event_ids

    def populate_locations(self):
        """populates database with all locations and region as dictated in settings"""

        locations = self.client.get('https://api.securevan.com/v4/locations').json().pop('items')

        for location in locations:
            location_id = location.get('locationId')
            name = location.get('name')
            location = location.pop('address')
            if location != None:
                state = location.get('stateOrProvince', "Distributed")
                region = settings.get('regions').get(state, "Distributed")
                
            else:
                region = ""
        
            new_location = Location(location_id, name, region)
            db.session.add(new_location)

        db.session.commit()

    def get_shifts_date(self, date=None):
        """returns all shifts of given date, otherwise all shifts today"""
        if not date:
            date = datetime.today().strftime('%Y-%m-%d')

        exists = Shift.query.filter_by(date=date).first()
        if exists:
            return date

        events = Event.query.filter_by(date=date).all()

        for event in events:

            signups = self.client.get('https://api.securevan.com/v4/signups?eventId={}'.format(event.event_id)).json().pop('items')

            for shift in signups:

                event_signup_id = shift.get('eventSignupId')
                event_shift_id = shift.get('shift').get('eventShiftId')
                van_id = shift.get('person').get('vanId')
                first_name = shift.get('person').get('firstName')
                last_name = shift.get('person').get('lastName')
                phone_number = shift.get('person').get('vanId')
                location = shift.get('location').get('locationId')
                status = shift.get('status').get('name')
                time = datetime.strptime(shift.get('startTimeOverride').replace(':', '')[11:], '%H%M%S%z').strftime('%I:%M %p')
            
                if Volunteer.query.filter_by(van_id=van_id).first() == None:
                    vol = self.client.get('https://api.securevan.com/v4/people/{}?$expand=phones'.format(van_id)).json()
                    
                    try:
                        for number in vol.get('phones'):
                            if number['isPreferred'] == True:
                                phone_number = number.get('phoneNumber')
                    except TypeError:
                        phone_number = ""

                    if shift.get('role').get('name') == "Intern":
                        new_vol = Volunteer(van_id, first_name, last_name, phone_number, True)
                    else:
                        new_vol = Volunteer(van_id, first_name, last_name, phone_number)
                    
                    db.session.add(new_vol)
            
                
                new_shift = Shift(event_signup_id, event_shift_id, time, date, status, event.event_id, van_id, location)
                db.session.add(new_shift)
            
        db.session.commit()

        return date

    def setup(self):
        """initial setup"""
        self.get_event_ids()
        self.populate_locations()
        self.get_shifts_date()
        
def main():
    db.drop_all()
    db.create_all()
    api = CPTVANAPI(settings)
    api.setup()

if __name__ == '__main__':
    main()
