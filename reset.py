from models import db, engine, Volunteer, Shift, Location, Note, CanvassGroup, create_view, drop_view, Table, MetaData, engine
from setup_config import dashboard_query

    

def main():
    engine.execute('DROP VIEW consolidated.dashboard_totals')
    Note.__table__.drop(engine)
    Shift.__table__.drop(engine)
    CanvassGroup.__table__.drop(engine)
    Location.__table__.drop(engine)
    Volunteer.__table__.drop(engine)
    Location.__table__.create(engine)
    Volunteer.__table__.create(engine)
    CanvassGroup.__table__.create(engine)
    Shift.__table__.create(engine)
    Note.__table__.create(engine)
    engine.execute(dashboard_query)
    

if __name__ == '__main__':
    main()
    
    