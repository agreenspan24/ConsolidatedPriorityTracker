from models import CanvassGroup, Shift, BackupGroup, BackupShift
from app import db

def backup():
    groups = CanvassGroup.query.all()

    for group in groups:
        backup_group = BackupGroup(group)
        db.session.add(backup_group)
        db.session.commit()

        for shift in group.canvass_shifts:
            backup_shift = BackupShift(shift)
            backup_shift.canvass_group = backup_group.id

            db.session.add(backup_shift)

    other_shifts = Shift.query.filter(Shift.canvass_group == None).all()

    for shift in other_shifts:
        backup_shift = BackupShift(shift)
        db.session.add(backup_shift)

    db.session.commit()

def main():
    backup()

if __name__ == '__main__':
    main()