from datetime import datetime

from flask import flash, g, redirect, render_template, request, session

from app import app
from config import settings
from cptvanapi import CPTVANAPI
from models import EventParticipant, EventParticipantStats


@app.before_request
def api():
    g.api = CPTVANAPI(settings)
    g.api.get_shifts_date()

@app.route('/', methods=['POST','GET'])
def index():
    offices = map(lambda x: x.location, EventParticipant.query(func.count(distinct(location))))
    if request.method == 'POST':
        office = request.form.get('office')
        confirms = EventParticipant.query.filter_by(location=office).all()
        stats = EventParticipantStats(confirms)
        return render_template('same_day_confirms.html', api=g.api, offices=offices, confirms=confirms, stats=stats)

    return render_template('same_day_confirms.html', api=g.api, offices=offices, confirms=None, stats=None)

@app.route('/shifts', methods=['GET','POST'])
def test():
    office = request.args.get('office')
    region = request.args.get('region')
    date = request.args.get('date')
    date = g.api.get_shifts_date(date)

    if office:
            
        shifts = Shift.query.filter_by(shift_location=office, date=date).all()   
        return render_template('shifts.html', shifts=shifts)
    
    if region:
        #TODO
        return None


if __name__ == "__main__":
    app.run()
