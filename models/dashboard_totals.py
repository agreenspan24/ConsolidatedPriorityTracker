from app import engine, db, app, schema
from sqlalchemy import Table, MetaData, Column
import os

# Represents a View in the database with all the details desired for admins on the dashboard.
class DashboardTotal(db.Model):
    __table__ = Table('dashboard_totals', MetaData(),
        Column('region', db.String(2)),
        Column('office', db.String(50), primary_key=True),
        Column('canvass_total_scheduled', db.BigInteger),
        Column('canvass_same_day_confirmed', db.BigInteger),
        Column('canvass_same_day_confirmed_perc', db.Numeric),
        Column('canvass_completed', db.BigInteger),
        Column('canvass_completed_perc', db.Numeric),
        Column('canvass_declined', db.BigInteger),
        Column('canvass_declined_perc', db.Numeric),
        Column('canvass_flaked', db.BigInteger),
        Column('canvass_flaked_perc', db.Numeric),
        Column('phone_total_scheduled', db.BigInteger),
        Column('phone_same_day_confirmed', db.BigInteger),
        Column('phone_same_day_confirmed_perc', db.Numeric),
        Column('phone_completed', db.BigInteger),
        Column('phone_completed_perc', db.Numeric),
        Column('phone_declined', db.BigInteger),
        Column('phone_declined_perc', db.Numeric),
        Column('phone_flaked', db.BigInteger),
        Column('phone_flaked_perc', db.Numeric),
        Column('flake_total', db.BigInteger),
        Column('flake_attempts', db.BigInteger),
        Column('flake_attempts_perc', db.Numeric),
        Column('flake_rescheduled', db.BigInteger),
        Column('flake_rescheduled_perc', db.Numeric),
        Column('flake_chase_remaining', db.BigInteger),
        Column('flake_chase_remaining_perc', db.Numeric),
        Column('shifts_unpitched', db.BigInteger),
        Column('shifts_unpitched_perc', db.Numeric),
        Column('extra_shifts_sched', db.BigInteger),
        Column('canvassers_all_day', db.Numeric),
        Column('actual_all_day', db.BigInteger),
        Column('goal_all_day', db.BigInteger),
        Column('packets_out_all_day', db.BigInteger),
        Column('kps', db.Numeric),
        Column('canvassers_out_now', db.Numeric),
        Column('actual_out_now', db.BigInteger),
        Column('goal_out_now', db.BigInteger),
        Column('packets_out_now', db.BigInteger),
        Column('kph', db.Numeric),
        Column('overdue_check_ins', db.BigInteger),
        autoload=True, autoload_with=engine, schema=schema)

