from sqlalchemy import create_engine
from models import Volunteer, Shift, Location, Note, CanvassGroup
from app import engine

def main():
    #engine.execute('DROP VIEW  IF EXISTS consolidated.dashboard_totals')
    #Note.__table__.drop(engine)
    #Shift.__table__.drop(engine)
    #CanvassGroup.__table__.drop(engine)
    #Location.__table__.drop(engine)
    #Volunteer.__table__.drop(engine)
    #Location.__table__.create(engine)
    #Volunteer.__table__.create(engine)
    #CanvassGroup.__table__.create(engine)
    Shift.__table__.create(engine)
    Note.__table__.create(engine)
    

if __name__ == '__main__':
    main()
    
    