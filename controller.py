from datetime import datetime

from flask import flash, g, redirect, render_template, request, session

from app import app
from config import settings
from cptvanapi import CPTVANAPI
from models import Event, Location, Shift, Volunteer


@app.before_request
def api():
    g.api = CPTVANAPI(settings)
    g.api.get_shifts_date()
@app.route('/', methods=['POST','GET'])
def index():

    offices = Location.query.all()
    if request.method == 'POST':
        office = request.form.get('office')
        date = g.api.get_shifts_date()
        shifts = Shift.query.filter_by(shift_location=office, date=date).all()


        return render_template('same_day_confirms.html', api=g.api, offices=offices, confirms=shifts, )


    return render_template('filter.html', api=g.api, offices=offices, confirms=None, stats=None)

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
