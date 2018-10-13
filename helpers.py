from app import app, db, engine
from models import db, SyncShift, Volunteer, Shift, Location
from datetime import datetime
from setup_config import black_list, rural_locations

def update_shifts():
    today = datetime.now().date()
    date = today.strftime('%Y-%m-%d')
    syncshifts = SyncShift.query.filter_by(startdate=date).all()
    
    for today_shift in syncshifts:
        update_shifts = Shift.query.filter_by(date=today_shift.startdate, time=today_shift.starttime, eventtype=today_shift.eventtype).all()
        if update_shifts:
            update_shift = next((x for x in update_shifts if x.volunteer.van_id == today_shift.vanid), None)

            if not update_shift:
                if today_shift.locationid is not None:
                    location = Location.query.filter_by(locationid=today_shift.locationid).first()

                    if not location:
                        location = Location(today_shift.locationid, today_shift.locationname, rural_locations.get(today_shift.locationname, today_shift.locationname), today_shift.locationname[0:2])
                        db.session.add(location)
                
                volunteer = Volunteer.query.filter_by(van_id=today_shift.vanid).first()

                if not volunteer:
                    firstname = today_shift.firstname if today_shift.firstname else '_____'
                    lastname = today_shift.lastname if today_shift.lastname else '_____'

                    volunteer = Volunteer(today_shift.vanid, firstname, lastname, today_shift.phone, today_shift.mobilephone)
                    db.session.add(volunteer)
                    db.session.commit()

                if volunteer.next_shift == None or volunteer.next_shift <= today:
                    next_shift = SyncShift.query.filter(SyncShift.vanid==today_shift.vanid, SyncShift.startdate>date).order_by(SyncShift.startdate).first()
                    if next_shift:
                        volunteer.next_shift = next_shift.startdate

                if today_shift.status in ['Invited', 'Left Msg', 'Confirmed', 'Scheduled', 'Sched-Web']:
                    update_shift = Shift(today_shift.eventtype, today_shift.starttime, today_shift.startdate, today_shift.status, today_shift.role, volunteer.id, location.locationid)
                    db.session.add(update_shift)

    db.session.commit()


def main():
    update_shifts()


if __name__ == '__main__':
    main()
        


