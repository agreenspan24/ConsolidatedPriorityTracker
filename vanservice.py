import requests
import simplejson
from requests.auth import HTTPBasicAuth
from Flask import jsonify

class VanService():

    def __init__(self, settings):

        self.client = requests.Session()
        self.client.auth = (os.environ('api_key'), os.environ('api_pass'))

    def sync_status(signup_id, status):

        data = {
            'eventSignupId': signup_id,
            'status': {
                'statusId': status
            }
        }

        self.client.put('https://api.securevan.com/v4/signups/' + signup_id, data=jsonify(data))
        