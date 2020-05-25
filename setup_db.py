from sqlalchemy import create_engine
from models import Volunteer, Shift, Location, Note, CanvassGroup, BackupGroup, BackupShift, User
from app import engine, db, schema
from setup_config import dashboard_query, users_query
from backup import backup
import os

def main():
    print('Creating tables in schema: ' + schema)

    Location.__table__.create(engine)
    Volunteer.__table__.create(engine)
    User.__table__.create(engine)
    CanvassGroup.__table__.create(engine)
    Shift.__table__.create(engine)
    Note.__table__.create(engine)
    
    engine.execute(dashboard_query.format(schema))
    engine.execute(users_query.format(schema))

    BackupGroup.__table__.create(engine)
    BackupShift.__table__.create(engine)

if __name__ == '__main__':
    main()
    
    