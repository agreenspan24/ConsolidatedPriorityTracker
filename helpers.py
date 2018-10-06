from app import app, db
from models import db, SyncShift, Volunteer, Shift, Location, 
from datetime import datetime
from config import black_list

def update_shifts():
    date = datetime.today().strftime('%Y-%m-%d')
    syncshifts = SyncShift.query.filter_by(startdate=date).all()
    
    for today_shift in syncshifts:
        update_shift = Shift.query.filter_by(date=today_shift.startdate, time=today_shift.starttime, person=today_shift.vanid).all()
        print(update_shift)

        if not update_shift and update_shift.locationname not in black_list:
            location = Location.query.filter_by(locationid=today_shift.locationid).first()
            if not location:
                location = Location(today_shift.locationid, today_shift.locationname, today_shift.locationname[0:2])
                db.session.add(location)
            
            volunteer = Volunteer.query.filter_by(van_id=today_shift.vanid).first()
            if not volunteer:
                volunteer = Volunteer(today_shift.vanid, today_shift.firstname, today_shift.lastname, today_shift.phone, today_shift.mobilephone)
                db.session.add(volunteer)
                db.session.commit()
                volunteer = Volunteer.query.filter_by(van_id=today_shift.vanid).first()
            

            
            update_shift = Shift(today_shift.eventtype, today_shift.starttime, today_shift.startdate, today_shift.status, today_shift.role, volunteer.id, location.locationid)
            db.session.add(update_shift)

    db.session.commit()


def main():
    update_shifts()


if __name__ == '__main__':
    main()
        


