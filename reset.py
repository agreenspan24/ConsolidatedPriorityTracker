from models import db, engine, Volunteer, Shift, Location, Note, CanvassGroup, create_view, drop_view, dashboard_view
from config import consolidated_dashboard


def main():
    drop_view(dashboard_view, consolidated_dashboard)
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
    create_view(dashboard_view, if_exists=True)
    


if __name__ == '__main__':
    main()