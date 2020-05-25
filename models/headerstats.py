from app import db
from sqlalchemy import Table, Column
from datetime import datetime, timedelta

'''
Governs the pips in the header tabs that show unflipped shifts, 
overdue checkins and flakes not chased
'''
class HeaderStats:
    def __init__(self, shifts, groups):
        time_now = datetime.now()
        overdue = (time_now - timedelta(minutes=20)).time()
        flipped_status = ['In', 'Resched', 'No Show', 'Completed', 'Declined']

        self.unflipped_shifts = sum(1 for x in shifts if x.time < overdue and not x.status in flipped_status)
        self.overdue_check_ins = sum(1 for x in groups if not x.is_returned and x.check_in_time != None and x.check_in_time < time_now.time())
        self.flakes_not_chased = sum(1 for x in shifts if x.flake and x.status == 'No Show' and x.flake_pass < 1)



