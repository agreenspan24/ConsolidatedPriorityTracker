import requests
from requests.auth import HTTPBasicAuth
from flask import jsonify, Response
import json
import os
from models import ShiftStatus, Shift, EventType, SyncShift
from datetime import datetime, time, timedelta
from dateutil.parser import parse
from app import app, db

class VanService:

    def __init__(self):

        self.client = requests.Session()
        self.client.auth = (os.environ['api_user'], os.environ['api_key'] + '|1')
        self.client.headers.update({
            "user": os.environ['api_user'] + ":" + os.environ['api_key'] + '|1',
            "Content-Type": "application/json"
        })
        
        self.api_url = 'https://api.securevan.com/v4/'

    def sync_shifts(self, shift_ids):
        event_type_dict = {}

        shifts = Shift.query.filter(Shift.id.in_(shift_ids)).all()

        for shift in shifts:
            if shift.eventtype in event_type_dict.keys():
                event_type_dict[shift.eventtype].append(shift.id)
            else: 
                event_type_dict[shift.eventtype] = [shift.id]

        self.yesterday = datetime.today() - timedelta(days=1)
        self.tomorrow = datetime.today() + timedelta(days=1)

        unflipped_shifts = []
        success = True
        
        for key, shift_ids in event_type_dict.items():
            events = self.get_events(key)

            if not events or len(events) < 1:
                return Response('Could not find events', 400)

            unflipped_shifts = shift_ids

            for event in events:
                if len(unflipped_shifts) == 0:
                    break
                
                shift_ids = unflipped_shifts
                unflipped_shifts = []

                signups_json = self.client.get(self.api_url + 'signups?eventId=' + str(event['eventId'])).json()

                signups = list(signups_json['items'])

                for shift_id in shift_ids:
                    shift = next(x for x in shifts if x.id == shift_id)

                    signup = next((x for x in signups if x['person']['vanId'] == shift.volunteer.van_id and parse(x['startTimeOverride']).time() == shift.time), None)

                    if signup:
                        if signup['status']['statusId'] != shift.status:
                            response = update_status(signup, shift.status)

                            if response.status_code < 400:
                                shift.shift_flipped = True
                            else: 
                                return Response('Error updating shifts', 400)
                        else:
                            shift.shift_flipped = True

                    else:
                        unflipped_shifts.append(shift_id)

            if len(unflipped_shifts) > 0:
                success = False   

        db.session.commit()

        return success

    def get_events(self, eventtype):
        eventType = EventType.query.filter_by(name=eventtype).first()

        queryString = '?eventTypeIds=' + str(eventType.id) + '&startingAfter=' + self.yesterday.strftime('%Y-%m-%d') + '&startingBefore=' + self.tomorrow.strftime('%Y-%m-%d')
        events = self.client.get(self.api_url + 'events' + queryString).json()

        return list(events['items'])


    def confirm_next_shift(self, vanid):
        signups_json = self.client.get(self.api_url + 'signups?vanId=' + vanid).json()

        signups = list(signups_json['items']) #puts in ascending date order
        print('signups[0]', signups[0])
        if not signups:
            return Response('Shifts not found', 400)

        signups.reverse()
    
        next_shift = next((x for x in signups if parse(x['startTimeOverride']).date() > datetime.today().date()), None)
        print('next_shift', next_shift)
        if next_shift and next_shift['status']['name'] != 'Confirmed':
            response = self.update_status(next_shift, 'Confirmed')
            print(response)

            if response.status_code < 400:
                shift.shift_flipped = True
                return True
            else: 
                return Response('Error updating shift', 400)

        return False


    def update_status(self, signup, status):
        status = ShiftStatus.query.filter_by(name=status).first()

        signup['status'] = {
            'statusId': status.id,
        }

        print('this would be flipped', signup)

        response = self.client.put(self.api_url + 'signups/' + str(signup['eventSignupId']), data=json.dumps(signup))
