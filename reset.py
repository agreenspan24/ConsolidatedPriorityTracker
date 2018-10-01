from models import db, engine, Volunteer, Shift, Location


def main():
    Shift.__table__.drop(engine)
    Location.__table__.drop(engine)
    Volunteer.__table__.drop(engine)
    Location.__table__.create(engine)
    Volunteer.__table__.create(engine)
    Shift.__table__.create(engine)


if __name__ == '__main__':
    main()