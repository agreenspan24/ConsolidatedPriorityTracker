from models import db, engine, Volunteer, Shift, Location, Note, CanvassGroup


def main():
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


if __name__ == '__main__':
    main()