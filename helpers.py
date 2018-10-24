from app import app, db, engine
from models import db, SyncShift, Volunteer, Shift, Location
from datetime import datetime
from setup_config import black_list, rural_locations

def update_shifts():
    today = datetime.now().date()
    date = today.strftime('%Y-%m-%d')
    syncshifts = SyncShift.query.filter_by(startdate=date).all()
    the_void = Location.query.get(1)
    
    for today_shift in syncshifts:
        print('vanid', today_shift.vanid)

        volunteer = Volunteer.query.filter_by(van_id=today_shift.vanid).first()

        if not volunteer:
            firstname = today_shift.firstname if today_shift.firstname else '_____'
            lastname = today_shift.lastname if today_shift.lastname else '_____'

            volunteer = Volunteer(today_shift.vanid, firstname, lastname, today_shift.phone, today_shift.mobilephone)
            db.session.add(volunteer)
            db.session.commit()
            
        volunteer.last_user = None
        volunteer.last_update = None

        volunteer.next_shift = None
        volunteer.next_shift_confirmed = False
        
        next_shift = SyncShift.query.filter(SyncShift.vanid==today_shift.vanid, today < SyncShift.startdate).order_by(SyncShift.startdate).first()
        if next_shift:
            print(next_shift.startdate)
            volunteer.next_shift = next_shift.startdate
            volunteer.next_shift_time = next_shift.starttime
        
            if next_shift.status == 'Confirmed':
                volunteer.next_shift_confirmed = True

        location = the_void
        if today_shift.locationname != None:
            location = Location.query.filter_by(actual_location_name=today_shift.locationname).first()

            if not location:
                location = Location(today_shift.locationid, today_shift.locationname, rural_locations.get(today_shift.locationname, today_shift.locationname), today_shift.locationname[0:2])
                db.session.add(location)

        update_shift = Shift.query.filter_by(date=today_shift.startdate, time=today_shift.starttime, eventtype=today_shift.eventtype, role=today_shift.role, shift_location=location.locationid, person=volunteer.id).first()
        if not update_shift:
            if today_shift.status in ['Invited', 'Left Msg', 'Confirmed', 'Scheduled', 'Sched-Web']:
                print('shift status', today_shift.status)
                update_shift = Shift(today_shift.eventtype, today_shift.starttime, today_shift.startdate, today_shift.status, today_shift.role, volunteer.id, location.locationid)
                db.session.add(update_shift)

        db.session.commit()


def main():
    update_shifts()


if __name__ == '__main__':
    main()
        


