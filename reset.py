from sqlalchemy import create_engine
from models import Volunteer, Shift, Location, Note, CanvassGroup, BackupGroup, BackupShift
from app import engine, db, schema
from setup_config import dashboard_query
from helpers import update_shifts
from backup import backup
import os

def main():
    print(schema)
    
    if schema == 'consolidated':
        backup()

    engine.execute('DROP VIEW IF EXISTS {0}.dashboard_totals'.format(schema))
    Note.__table__.drop(engine)
    Shift.__table__.drop(engine)
    CanvassGroup.__table__.drop(engine)
    CanvassGroup.__table__.create(engine)
    Shift.__table__.create(engine)
    Note.__table__.create(engine)

    engine.execute(dashboard_query.format(schema))

    update_shifts()
    

if __name__ == '__main__':
    main()
    
    