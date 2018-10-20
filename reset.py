from sqlalchemy import create_engine
from models import Volunteer, Shift, Location, Note, CanvassGroup, BackupGroup, BackupShift
from app import engine, db
from setup_config import dashboard_query
from helpers import update_shifts
from backup import backup
import os

def main():
    if os.environ['schema'] == 'consolidated':
        backup()

    engine.execute('DROP VIEW IF EXISTS {}.dashboard_totals'.format(os.environ['schema']))
    Note.__table__.drop(engine)
    Shift.__table__.drop(engine)
    CanvassGroup.__table__.drop(engine)
    CanvassGroup.__table__.create(engine)
    Shift.__table__.create(engine)
    Note.__table__.create(engine)
    engine.execute(dashboard_query.format(os.environ['schema']))

    update_shifts()
    

if __name__ == '__main__':
    main()
    
    