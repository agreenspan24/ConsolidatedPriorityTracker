from models import CanvassGroup, Shift, BackupGroup, BackupShift
from kps_responses import add_kps_responses
from datetime import datetime
from app import db

def backup():
    #add_kps_responses()

    groups = CanvassGroup.query.join(CanvassGroup.canvass_shifts).filter(Shift.date < datetime.now().date()).all()

    for group in groups:
        backup_group = BackupGroup(group)
        db.session.add(backup_group)
        db.session.commit()

        for shift in group.canvass_shifts:
            backup_shift = BackupShift(shift)
            backup_shift.canvass_group = backup_group.id

            db.session.add(backup_shift)

    other_shifts = Shift.query.filter(Shift.canvass_group == None, Shift.date < datetime.now().date()).all()

    for shift in other_shifts:
        backup_shift = BackupShift(shift)
        db.session.add(backup_shift)

    db.session.commit()

def main():
    backup()

if __name__ == '__main__':
    main()