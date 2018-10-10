from datetime import datetime

from flask import flash, g, redirect, render_template, request, session, abort, jsonify, escape, json, Response

from sqlalchemy import and_, asc

import re
import urllib

from app import app, oid

##from cptvanapi import CPTVANAPI
from models import db, Volunteer, Location, Shift, Note, User, ShiftStats, CanvassGroup, HeaderStats, SyncShift
from datetime import datetime
from vanservice import VanService
from dashboard_totals import DashboardTotal

vanservice = VanService()

oid.init_app(app)

@app.before_request
def logout_before():
    print(session)
    
    if request.path.startswith('/static') or request.path.startswith('/favicon'):
        return
    if request.path.startswith('/oidc_callback'):
        return

    g.time_now = datetime.now().time()

    g.user = None
    redir = False
    if 'openid' in session:
        g.user = User.query.filter(User.openid==session['openid']).first()
        print(g.user.email)
        if g.user == None or not g.user.is_allowed:
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
                user = User(user_info['email'], user_info['sub'])

            db.session.add(user)
            db.session.commit()
            g.user = user
            print(user)

            return redirect('/')    

@oid.require_login        
@app.route('/', methods=['GET'])    
def index():
    if g.user.office:
        return redirect('/consolidated/' + g.user.office[0:3] + '/sdc')

    return redirect('/consolidated')    

@app.route('/logout', methods=['GET'])
def logout():
    g.user = None
    session.pop('openid', None)
    return redirect('/login')

@oid.require_login
@app.route('/consolidated', methods=['POST','GET'])
def consolidated():
    
    if g.user.rank == None:
        region = g.user.region
        offices = Location.query.distinct(Location.locationname).filter_by(region=region).order_by(asc(Location.locationname)).all()
    else:
        offices = Location.query.distinct(Location.locationname).order_by(asc(Location.locationname)).all()
    
    if request.method == 'POST':
        option = request.form.get('target')

        if option == "Dashboard":
            return redirect('/dashboard/conf')

        office = request.form.get('office')
        page = request.form.get('page')

        office = escape(office)

        return redirect('/consolidated/' + str(office)[0:3] + '/' + page)

    user = User.query.filter_by(email=g.user.email).first()
    dashboard_permission = user.rank == 'DATA' or user.rank == 'FD'

    return render_template('index.html', offices=offices, show_dashboard=dashboard_permission)

@oid.require_login
@app.route('/consolidated/<office>/<page>', methods=['GET', 'POST'])
def office(office, page):
    date = datetime.today().strftime('%Y-%m-%d')

    office = escape(office)
    locations = Location.query.filter(Location.locationname.like(office + '%')).all()

    if not locations:
        return redirect('/consolidated')


    location_ids = list(map(lambda l: l.locationid, locations))

    shifts = Shift.query.filter(Shift.shift_location.in_(location_ids), Shift.date==date).order_by(asc(Shift.time), asc(Shift.person)).all()

    all_shifts = []
    extra_shifts = []

    for shift in shifts:
        if shift.status in ['Completed', 'Declined', 'No Show', 'Resched']:
            extra_shifts.append(shift)
        else: 
            all_shifts.append(shift)
    for shift in extra_shifts:
        all_shifts.append(shift)
        
    all_groups = CanvassGroup.query.all()
    groups = []

    for gr in all_groups:
        if gr.canvass_shifts[0].shift_location in location_ids and gr.canvass_shifts[0].id in list(map(lambda s: s.id, all_shifts)):
            groups.append(gr)

    header_stats = HeaderStats(all_shifts, groups)

    if page == 'sdc':
        return render_template('same_day_confirms.html', active_tab=page, header_stats=header_stats, office=office, shifts=all_shifts)

    elif page == 'kph':
        return render_template('kph.html', active_tab=page, header_stats=header_stats, office=office, shifts=all_shifts, groups=groups)

    elif page == 'flake':
        return render_template('flake.html', active_tab=page, header_stats=header_stats, office=office, shifts=all_shifts)

    elif page == 'review':
        stats = ShiftStats(all_shifts, groups)

        review_shifts = []
        sync_shifts = SyncShift.query.filter(SyncShift.locationid.in_(location_ids), SyncShift.startdate==date).all()
        for shift in all_shifts:
            if not shifts.status in ['Invited', 'Left Msg', 'Scheduled', 'Same Day Confirmed', 'In'] and not shift.volunteer.van_id == None:
                old_shift = find(lambda x: shift.volunteer.van_id == x.vanid and shift.time == x.starttime, sync_shifts)
                if not old_shift.status in ['Invited', 'Left Msg'] and old_shift.status != shift.status:
                    review_shifts.append(shift)

        return render_template('review.html', active_tab=page, header_stats=header_stats, office=office, stats=stats, shifts=review_shifts)

    else:
        return redirect('/consolidated/' + office + '/sdc')

@oid.require_login
@app.route('/consolidated/<office>/<page>/pass', methods=['POST'])
def add_pass(office, page):
    keys = list(request.form.keys())
    parent_id = request.form.get('parent_id')
    page_load_time = datetime.strptime(urllib.parse.unquote(request.form.get('page_load_time')), '%I:%M %p').time()
    has_note_text = 'note' in keys
    has_cellphone = 'cellphone' in keys
    has_vol_id = 'vol_id' in keys

    if not parent_id:
        return abort(400)

    return_var = None

    if page == 'kph':
        group = CanvassGroup.query.get(parent_id)

        if not group:
            return Response('Group Not Found', status=400)

        if group.updated_by_other(page_load_time, g.user):
            return Response('This Canvass Group has been updated by a different user since you last loaded the page. Please refresh and try again.', 400)
        
        if 'shift_id[]' in keys:
            shift_ids = request.form.getlist('shift_id[]')

            for id in shift_ids:
                if not id.isdigit():
                    return Response('Invalid shift id', status=400)

            shifts = group.update_shifts(shift_ids)
            for shift in shifts:
                if return_var == None:
                    return_var = []

                return_var.append({
                    'shift_id': shift.id,
                    'van_id': shift.volunteer.van_id,
                    'name': shift.volunteer.first_name + ' ' + shift.volunteer.last_name,
                    'phone': shift.volunteer.phone_number,
                    'cellphone': shift.volunteer.cellphone
                })

            return_var = jsonify(return_var)

        if 'out' in keys:
            group = group.setOut()

            return_var  = jsonify({
                'is_returned': group.is_returned,
                'departure': group.departure.strftime('%I:%M %p'), 
                'check_in_time': group.check_in_time.strftime('%I:%M %p') if group.check_in_time else '',
                'last_check_in': group.last_check_in.strftime('%I:%M %p'),
                'check_ins': group.check_ins
            })

        if 'actual' in keys:
            check_in_amount = request.form.get('actual')

            if check_in_amount and not check_in_amount.isdigit():
                return Response('Check In Amount must be a number"', status=400)

            group = group.check_in(check_in_amount)

            note = group.add_note('kph', check_in_amount + " doors")

            return_var = jsonify({
                'check_in_time': group.check_in_time.strftime('%I:%M %p'), 
                'last_check_in': group.last_check_in.strftime('%I:%M %p'),
                'check_ins': group.check_ins,
                'actual': group.actual,
                'note': note
            })

        if has_note_text:
            note_text = request.form.get('note')

            note_text = escape(note_text)

            return_var = group.add_note(page, note_text)
            
        if has_cellphone and has_vol_id:
            cellphone = request.form.get('cellphone')

            phone_sanitized = re.sub('[- ().+]', '', cellphone)

            if phone_sanitized and not phone_sanitized.isdigit():
                return Response('Invalid Phone', status=400)

            vol_id = request.form.get('vol_id')
            volunteer = Volunteer.query.get(vol_id)

            if not volunteer:
                return Response('Could not find volunteer', status=400)

            if volunteer.updated_by_other(page_load_time, g.user):
                return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

            volunteer.cellphone = phone_sanitized
            volunteer.last_user = g.user.id
            volunteer.last_update = datetime.now().time()
        
        if 'goal' in keys: 
            goal = request.form.get('goal')

            if goal and not goal.isdigit():
                return Response('"Goal" must be a number"', status=400)
            group.goal = int(goal)

        if 'packets_given' in keys:
            packets_given = request.form.get('packets_given')
            if packets_given and not packets_given.isdigit():
                return Response('"packets_given" must be a number"', status=400)

            group.packets_given = int(packets_given)

        if 'packet_names' in keys:
            packet_names = request.form.get('packet_names')
            packet_names = escape(packet_names)

            group.packet_names = packet_names

        group.last_update = datetime.now().time()
        group.last_user = g.user.id

    else: 
        shift = Shift.query.get(parent_id)

        if not shift:
            return Response('Shift not found', status=400)
        
        if shift.updated_by_other(page_load_time, g.user):
            return Response('This Shift has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)
        
        if 'status' in keys:
            status = request.form.get('status')
            status = escape(status)

            if not status in ['Completed', 'Declined', 'No Show', 'Resched', 'Same Day Confirmed', 'In', 'Scheduled', 'Invited', 'Left Message']:
                return Response('Invalid status', status=400)

            return_var = shift.flip(page, status)    

        if 'first' in keys:
            first = request.form.get('first_name')

            if shift.volunteer.updated_by_other(page_load_time, g.user):
                return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

            first = escape(first)
            shift.volunteer.first_name = first 

        if 'last' in keys:
            last = request.form.get('last_name')

            if shift.volunteer.updated_by_other(page_load_time, g.user):
                return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

            last = escape(last)
            shift.volunteer.last_name = last 
        
        if 'phone' in keys:
            phone = request.form.get('phone')

            if shift.volunteer.updated_by_other(page_load_time, g.user):
                return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

            phone_sanitized = re.sub('[- ().+]', '', phone)

            if phone_sanitized and not phone_sanitized.isdigit():
                return Response('Invalid Phone', status=400)
            
            shift.volunteer.phone_number = phone_sanitized 

        if has_cellphone:
            cellphone = request.form.get('cellphone')
            
            if shift.volunteer.updated_by_other(page_load_time, g.user):
                return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

            phone_sanitized = re.sub('[- ().+]', '', cellphone)

            if phone_sanitized and not phone_sanitized.isdigit():
                return Response('Invalid Phone', status=400)

            shift.volunteer.cellphone = phone_sanitized
            shift.volunteer.last_user = g.user.id
            shift.volunteer.last_update = datetime.now().time()

        if has_note_text:
            note_text = request.form.get('note')

            note_text = escape(note_text)

            return_var = shift.add_note(page, note_text)

        if 'passes' in keys:
            return_var = str(shift.add_pass())
        
        shift.last_update = datetime.now().time()
        shift.last_user = g.user.id

    db.session.commit()

    if return_var:
        return return_var
    else:
        return ''

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

    group.update_shifts(shift_ids)

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
    phone_sanitized = ''

    if firstname:
        firstname = escape(firstname)

    if lastname: 
        lastname = escape(lastname)

    if phone:
        phone_sanitized = re.sub('[- ().+]', '', phone)

        if not phone_sanitized.isdigit():
            return abort(400, 'Invalid Phone')
        
    if time and not time in ['10:00 AM', '1:00 PM', '4:00 PM', '6:00 PM']:
        return abort(400, 'Invalid time')

    if role and not role in ['Canvassing', 'Phonebanking', 'Comfort Vol', 'Intern Onboarding', 'Intern Interview']:
        return abort(400, 'Invalid activity')

    eventtype = "Volunteer DVC" if role in ['Canvassing', 'Phonebanking'] else role

    office = escape(office)
    location = Location.query.filter(Location.locationname.like(office + '%')).first()

    shift = Shift(eventtype, time, datetime.now().date(), 'In', role, None, location.locationid)

    vol = Volunteer(None, firstname, lastname, phone_sanitized, None)
    db.session.add(vol)
    db.session.commit()

    vol = Volunteer.query.filter_by(first_name=firstname, last_name=lastname, van_id=None).first()

    shift.person = vol.id
    db.session.add(shift)

    db.session.commit()

    return redirect('/consolidated/' + office + '/' + page)

@oid.require_login
@app.route('/consolidated/<office>/sync_to_van', methods=['POST'])
def sync_to_van(office):

    vanids = request.form.getlist('vanids[]')
    statuses = request.form.getlist('statuses[]')
    
    for i, id in enumerate(vanids):
        print(statuses[i], vanids[i])
        vanservice.sync_shifts(statuses[i])

    return redirect('/consolidated/' + office + '/review')

@oid.require_login
@app.route('/dashboard/<page>', methods=['GET'])
def dashboard(page):
    dashboard_permission = g.user.rank == 'DATA' or g.user.rank == 'FD'

    if not dashboard_permission:
        return redirect('/consolidated')
    
    totals = DashboardTotal.query.all()

    if page == 'prod':

        return render_template('dashboard_production.html', active_tab=page, results=totals)

    elif page == 'top':
        return render_template('dashboard_toplines.html', active_tab=page, results=totals)

    return render_template('dashboard.html', active_tab=page, results=totals)

@oid.require_login
@app.route('/consolidated/<office>/<page>/recently_updated', methods=['GET'])
def get_recently_updated(office, page):
    page_load_time = datetime.strptime(urllib.parse.unquote(request.args.get('page_load_time')), '%I:%M %p').time()

    office = escape(office)
    locations = Location.query.filter(Location.locationname.like(office + '%')).all()
    location_ids = list(map(lambda l: l.locationid, locations))

    update_ids = []

    if page == 'kph':
        all_groups = CanvassGroup.query.all()

        for gr in all_groups:
            if (gr.canvass_shifts[0].shift_location in location_ids) and gr.updated_by_other(page_load_time, g.user):
                update_ids.append(gr.id)

    else:
        shifts = Shift.query.filter(Shift.shift_location.in_(location_ids)).all()
        
        for shift in shifts:
            if shift.updated_by_other(page_load_time, g.user):
                update_ids.append(shift.id)

    return jsonify(update_ids)

@oid.require_login
@app.route('/consolidated/<office>/<page>/delete_element', methods=['DELETE'])
def delete_element(office, page):
    parent_id = request.form.get('parent_id')
    name = ''

    if page == 'kph':
        group = CanvassGroup.query.get(parent_id)
        name = ','.join(list(map(lambda s: s.volunteer.first_name + ' ' + s.volunteer.last_name, group.canvass_shifts)))
        db.session.delete(group)
    
    else: 
        shift = Shift.query.get(parent_id)

        if shift.canvass_group:
            return Response('Please delete shift from canvass group first', 400)
            
        name = shift.volunteer.first_name + ' ' + shift.volunteer.last_name
        db.session.delete(shift)

    db.session.commit()
    return name

@oid.require_login
@app.route('/consolidated/<office>/<page>/delete_note', methods=['DELETE'])
def delete_note(office, page):
    shift_id = request.form.get('shift_id')
    text = request.form.get('text')
    print(shift_id, text)

    note = Note.query.filter_by(type=page, text=text, note_shift=shift_id).first()
    db.session.delete(note)
    db.session.commit()

    return ''

@oid.require_login
@app.route('/user', methods=['GET', 'POST'])
def user():
    offices = Location.query.order_by(asc(Location.locationname)).all()

    if request.method == "POST":
        user = User.query.get(g.user.id)

        firstname = request.form.get('firstname')
        print(user.id, firstname)

        if firstname:
            firstname = escape(firstname)
            user.firstname = firstname

        lastname = request.form.get('lastname')

        if lastname:
            lastname = escape(lastname)
            user.lastname = lastname

        fullname = request.form.get('fullname')

        if fullname:
            fullname = escape(fullname)
            user.fullname = fullname

        office = request.form.get('office')

        office = escape(office)
        user.office = office

        db.session.commit()

    return render_template('user.html', offices=offices)

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
