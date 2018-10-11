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
        
        for key, shift_ids in event_type_dict.items():
            event = self.get_event(key)

            if not event:
                return Response('Could not find event', 400)

            signups_json = self.client.get('https://api.securevan.com/v4/signups?eventId=' + str(event['eventId'])).json()

            signups = list(signups_json['items'])

            for shift_id in shift_ids:
                shift = next(x for x in shifts if x.id == shift_id)

                signup = next((x for x in signups if x['person']['vanId'] == shift.volunteer.van_id and parse(x['startTimeOverride']).time() == shift.time), None)

                if signup:
                    status = ShiftStatus.query.filter_by(name=shift.status).first()

                    if signup['status']['statusId'] != shift.status:
                        signup['status'] = {
                            'statusId': status.id,
                        }

                        print('this would be flipped', signup)
                
                        #response = self.client.put('https://api.securevan.com/v4/signups/' + str(signup['eventSignupId']), data=json.dumps(signup))

                        #if response.status_code < 400:
                            #shift.shift_flipped = True
                        #else: 
                            #return Response('Error updating shifts', 400)
                    else:
                        shift.shift_flipped = True

                else:
                    unflipped_shifts.append(shift_id)

            db.session.commit()

        return len(unflipped_shifts) > 0

    def get_event(self, eventtype):
        eventType = EventType.query.filter_by(name=eventtype).first()

        queryString = 'eventTypeIds=' + str(eventType.id) + '&startingAfter=' + self.yesterday.strftime('%Y-%m-%d') + '&startingBefore=' + self.tomorrow.strftime('%Y-%m-%d')
        events = self.client.get('https://api.securevan.com/v4/events?' + queryString).json()

        return next((x for x in list(events['items'])), None)
