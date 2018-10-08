import requests
import simplejson
from requests.auth import HTTPBasicAuth
from Flask import jsonify

class VanService():

    def __init__(self, settings):
        
        os.environ('api_user') = 'demo.wzigler.api'
        os.environ('api_key') = 'a95c16b1-34e8-abd7-adb6-44a6eb232ef8'

        self.client = requests.Session()
        self.client.auth = (os.environ('api_user'), os.environ('api_key'))
        self.client.headers.update({
            "user": "demo.wzigler.api:a95c16b1-34e8-abd7-adb6-44a6eb232ef8|1",
            "Content-Type": "application/json"
        })

    def sync_status(signup_id, status):

        data = {
            'eventSignupId': 26250,
            'status': {
                'statusId': status
            }
        }

        result = self.client.get('https://api.securevan.com/v4/signups/' + 26250, data=jsonify(data))
        print(result)
        