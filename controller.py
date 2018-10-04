from datetime import datetime

from flask import flash, g, redirect, render_template, request, session, abort, jsonify, escape

from sqlalchemy import and_, asc

import re

from app import app, oid
from config import settings
##from cptvanapi import CPTVANAPI
from models import db, Volunteer, Location, Shift, Note, User, ShiftStats, CanvassGroup, DashboardTotal
from datetime import datetime

oid.init_app(app)

@app.before_request
def logout_before():
    print(session)
    if request.path.startswith('/static') or request.path.startswith('/favicon'):
        return
    if request.path.startswith('/oidc_callback'):
        return

    g.user = None
    redir = False
    if 'openid' in session:
        g.user = User.query.filter(User.openid==session['openid']).first()
        if g.user == None:
            redir = True
    else:
        redir = True
    if redir and not request.path.startswith('/login'):
        return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login_page():
    if request.method == 'POST':
        return redirect('/login_auth')
    return render_template('login.html', next='/login_auth')

@app.route('/login_auth', methods=['GET','POST'])
@oid.require_login
def login_auth():
    if 'user' in g:
        if g.user is not None:
            return redirect('/consolidated')
    if g.oidc_id_token is None: # Token is stale
        print('Something wicked, no token in g')
    elif 'oidc_id_token' in g:
        if False: #Placeholder, can remove
            pass
        else:
            user_info = oid.user_getinfo(['sub','email'])
            session['openid'] = user_info['sub']
            user = User.query.filter_by(email=user_info['email']).first()
            if user is not None and user.openid is None:
                user.openid = user_info['sub']
            elif user is None:
                user = User()
                user.openid = user_info['sub']
                user.email = user_info['email']

            db.session.add(user)
            db.session.commit()
            g.user = user
            print(user)
            return redirect('/consolidated')    
@oid.require_login        
@app.route('/', methods=['GET'])    
def index():
    return redirect('/consolidated')    

@app.route('/logout', methods=['GET'])
def logout():
    g.user = None
    session.pop('openid', None)
    return redirect('/login')

@oid.require_login
@app.route('/consolidated', methods=['POST','GET'])
def consolidated():
    offices = Location.query.order_by(asc(Location.locationname)).all()
    if request.method == 'POST':
        option = request.form.get('target')

        if option == "Dashboard":
            return redirect('/dashboard')

        office = request.form.get('office')
        page = request.form.get('page')

        office = escape(office)

        return redirect('/consolidated/' + str(office)[0:3] + '/' + page)

    user = User.query.filter_by(email=g.user.email).first()
    dashboard_permission = user.rank == 'DATA' or user.rank == 'FD'

    return render_template('index.html', user=g.user, offices=offices, show_dashboard=dashboard_permission)

@oid.require_login
@app.route('/consolidated/<office>/<page>', methods=['GET', 'POST'])
def office(office, page):
    date = datetime.today().strftime('%Y-%m-%d')

    office = escape(office)
    locations = Location.query.filter(Location.locationname.like(office + '%')).all()

    if not locations:
        return redirect('/consolidated')

    all_shifts = []
    extra_shifts = []
    for location in locations:
        shifts = Shift.query.filter_by(shift_location=location.locationid, date=date).order_by(asc(Shift.time), asc(Shift.person)).all()
        for shift in shifts:
            if shift.status in ['Completed', 'Declined'] or shift.flake == True:
                extra_shifts.append(shift)
            else: 
                all_shifts.append(shift)
        for shift in extra_shifts:
            all_shifts.append(shift)
        
        if page == 'kph':
            groups = CanvassGroup.query.all()

    if page == 'sdc':
        return render_template('same_day_confirms.html', active_tab="sdc", location=location, shifts=all_shifts)

    elif page == 'kph':
        return render_template('kph.html', active_tab="kph", location=location, shifts=all_shifts, groups=groups)

    elif page == 'flake':
        return render_template('flake.html', active_tab="flake", location=location, shifts=all_shifts)

    elif page == 'review':
        stats = ShiftStats(all_shifts)
        return render_template('review.html', active_tab="review", location=location, stats=stats, shifts=all_shifts)

    else:
        return redirect('/consolidated/' + office + '/sdc')

@oid.require_login
@app.route('/consolidated/<office>/<page>/pass', methods=['POST'])
def add_pass(office, page):
    parent_id = request.form.get('parent_id')
    note_text = request.form.get('note')
    cellphone = request.form.get('cellphone')
    van_id = request.form.get('van_id')

    if not parent_id:
        return abort(400)

    if page == 'kph':
        returned = request.form.get('returned')
        checked_in = 'checked_in' in request.form.keys()
        actual = request.form.get('actual')
        goal = request.form.get('goal')
        packets_given = request.form.get('packets_given')
        packet_names = request.form.get('packet_names')

        return_var = ""
        group = CanvassGroup.query.get(parent_id)

        if not group:
            return abort(400, 'Group Not Found')

        if returned:
            if not isinstance(returned, bool):
                return abort(400, 'Invalid value for "Returned"')

            group = group.returned(true)

            return_var  = jsonify({
                'last_check_in': group.last_check_in.strftime('%I:%M %p'),
                'check_ins': group.check_ins
            })

        if checked_in:
            group = group.check_in()
            return_var = jsonify({
                'departure': group.departure.strftime('%I:%M %p'), 
                'check_in_time': group.next_check_in.strftime('%I:%M %p'), 
                'last_check_in': group.last_check_in.strftime('%I:%M %p'),
                'check_ins': group.check_ins
            })

        if note_text:
            note_text = escape(note_text)

            group.add_note(page, note_text)
        
        if cellphone:
            phone_sanitized = re.sub('() -+', '', cellphone)

            if not phone_sanitized.isdigit():
                return abort(400, 'Invalid Phone')

            volunteer = Volunteer.query.filter_by(van_id=van_id).first()
            volunteer.cellphone = cellphone

        if actual:
            if not actual.isdigit():
                return abort(400, '"Actual" must be a nuber"')

            group.actual = int(actual)
        
        if goal: 
            if not goal.isdigit():
                return abort(400, '"Goal" must be a nuber"')
            group.goal = int(goal)

        if packets_given:
            if not packets_given.isdigit():
                return abort(400, '"packets_given" must be a nuber"')

            group.packets_given = int(packets_given)

        if packet_names:
            packet_names = escape(packet_names)

            group.packet_names = packet_names
        
        db.session.commit()
        return return_var
    else: 
        status = request.form.get('status')

        shift = Shift.query.get(parent_id)

        if not shift:
            return abort(400, 'Shift not found')
        
        if status:
            status = escape(status)

            if not status in ['Completed', 'Declined', 'No Show', 'Resched', 'Same Day Confirmed', 'In', 'Scheduled', 'Invited', 'Left Message']:
                return abort(400, 'Invalid status')

            shift.flip(status)     

        if note_text:
            note_text = escape(note_text)

            shift = Shift.query.get(parent_id)
            return_var = shift.add_call_pass(page, note_text)

        if cellphone:
            phone_sanitized = re.sub('() -+.', '', cellphone)

            if not phone_sanitized.isdigit():
                return abort(400, 'Invalid Phone')

            volunteer = Volunteer.query.filter_by(van_id=van_id).first()
            volunteer.cellphone = cellphone

        db.session.commit()
        return return_var

@oid.require_login
@app.route('/consolidated/<office>/<page>/add_group', methods=['POST'])
def add_group(office, page):
    group = CanvassGroup()

    shift_ids = request.form.getlist('shift_id[]')
    goal = request.form.get('goal')
    packets_given = request.form.get('packets_given')
    packet_names = request.form.get('packet_names')

    for id in shift_ids:
        if not id.isdigit():
            return abort(400, 'Invalid shift id')

    group.add_shifts(shift_ids)

    if goal:
        if not goal.isdigit():
            return abort(400, 'Goal must be a number')
        
        group.goal = int(goal)
    
    if packets_given:
        if not goal.isdigit():
            return abort(400, '# of Packets must be a number')

        group.packets_given = int(packets_given)

    if packet_names:
        packet_names = escape(packet_names)
        
        group.packet_names = packet_names

    db.session.add(group)
    db.session.commit()

    return redirect('/consolidated/' + office + '/kph')

@oid.require_login
@app.route('/consolidated/<office>/<page>/walk_in', methods=['POST'])
def add_walk_in(office, page):
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    phone = request.form.get('phone')
    time = request.form.get('time')
    role = request.form.get('activity')

    if firstname:
        firstname = escape(firstname)

    if lastname: 
        lastname = escape(lastname)

    if phone:
        phone_sanitized = re.sub('() -+.', '', phone)

        if not phone_sanitized.isdigit():
            return abort(400, 'Invalid Phone')
        
    if time and not time in ['10:00 AM', '1:00 PM', '4:00 PM', '6:00 PM']:
        return abort(400, 'Invalid time')

    if role and not role in ['Canvassing', 'Phonebanking', 'Comfort Vol', 'Intern Onboarding', 'Intern Interview']:
        return abort(400, 'Invalid activity')

    eventtype = "Volunteer DVC" if role in ['Canvassing', 'Phonebanking'] else role

    office = escape(office)
    location = Location.query.filter(Location.locationname.like(office + '%')).first()

    shift = Shift(eventtype, time, datetime.now().date(), 'Confirmed', role, None, location.locationid)

    vol = Volunteer(None, firstname, lastname, phone, None)
    db.session.add(vol)
    db.session.commit()

    vol = Volunteer.query.filter_by(first_name=firstname, last_name=lastname, van_id=None).first()

    shift.person = vol.id
    db.session.add(shift)

    db.session.commit()

    return redirect('/consolidated/' + office + '/' + page)

@oid.require_login
@app.route('/dashboard')
def dashboard():
    user = User.query.filter_by(email=g.user.email).first()
    dashboard_permission = user.rank == 'DATA' or user.rank == 'Field Director'

    if not dashboard_permission:
        return redirect('/consolidated')
    
    totals = DashboardTotal.query.all()
    return render_template('dashboard.html', results=totals)

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/consolidated')

@app.errorhandler(500)
def internal_service_error(e):
    if request.endpoint == 'pass':
        return abort(500)

    return redirect('/consolidated')

if __name__ == "__main__":
    app.run()
