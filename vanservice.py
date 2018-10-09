import requests
from requests.auth import HTTPBasicAuth
from flask import jsonify
import json
import os
from models import ShiftStatus

class VanService:

    def __init__(self):
        print('init')
        os.environ['api_user'] = 'demo.wzigler.api'
        os.environ['api_key'] = 'a95c16b1-34e8-abd7-adb6-44a6eb232ef8|1'

        self.client = requests.Session()
        self.client.auth = (os.environ['api_user'], os.environ['api_key'])
        self.client.headers.update({
            "user": os.environ['api_user'] + ":" + 'a95c16b1-34e8-abd7-adb6-44a6eb232ef8|1',
            "Content-Type": "application/json"
        })

    def sync_shifts(self, status):

        result = self.client.get('https://api.securevan.com/v4/signups/' + str(26250)).json()

        print(result)

        status = ShiftStatus.query.filter_by(name=status).first()

        result['status'] = {
            'statusId': status.id,
        }

        result = self.client.put('https://api.securevan.com/v4/signups/' + str(26250), data=json.dumps(result))

        print(result.text, result)

        return result
        