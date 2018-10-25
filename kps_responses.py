import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from oauth2client import file, client, tools
from googleapiclient.discovery import build
from httplib2 import Http
from models import CanvassGroup
import json

def add_kps_responses():
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))


    spreadsheet_id = "1wS0bPbCM0qsNWR2-7uMwH5MUwlW4HX3n2YEKeGqhx3s"
    range_ = "'Form Responses 1'!A1:D1"
    value_input_option = "USER_ENTERED" 
    insert_data_option = "INSERT_ROWS"

    responses = []
    timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S')

    vol_dict = {}
    groups = CanvassGroup.query.join(CanvassGroup.canvass_shifts).filter(CanvassGroup.is_active==True, CanvassGroup.is_returned==True, Shift.date < datetime.now().date()).all()

    date = groups[0].canvass_shifts[0].date

    for gr in groups:
        for shift in gr.canvass_shifts:
            if shift.volunteer.van_id != None and shift.eventtype != 'Out of State':
                if shift.volunteer.van_id in vol_dict.keys():
                    vol_dict[shift.volunteer.van_id] += gr.actual
                else:
                    vol_dict[shift.volunteer.van_id] = gr.actual

    for vanid, actual in vol_dict.items():
        responses.append([timestamp, vanid, date.strftime('%m/%d/%Y'), actual])

    data = {
        "range": range_,
        "majorDimension": "ROWS",
        "values": responses,
    }

    #print('this would be posted', data)

    response = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_, includeValuesInResponse=True, valueInputOption=value_input_option, insertDataOption=insert_data_option, body=data).execute()
    
    print(response['updates'])

def main():
    add_kps_responses()

if __name__ == '__main__':
    main()