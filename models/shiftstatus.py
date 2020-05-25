from app import db
from sqlalchemy import Table, Column

class ShiftStatus(db.Model):
    __table_args__ = {'schema':'consolidated'}
    __tablename__ = 'shiftstatus'

    id = db.Column('statusid', db.Integer, primary_key=True)
    name = db.Column('name', db.String(100))