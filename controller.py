from datetime import datetime

from flask import flash, g, redirect, render_template, request, session, abort, jsonify, escape, json, Response

from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import contains_eager, joinedload

import re
import urllib

from app import app, oid, schema

##from cptvanapi import CPTVANAPI
from models import db, Volunteer, Location, Shift, Note, User, ShiftStats, CanvassGroup, HeaderStats, SyncShift, BackupGroup, BackupShift
from datetime import datetime, timedelta
from dateutil.parser import parse
from vanservice import VanService
from dashboard_totals import DashboardTotal
import os

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

        if g.user == None or not g.user.is_allowed or (schema == 'test' and g.user.rank != 'DATA'):
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

    if g.user.office and g.user.office != "None":
        return redirect('/consolidated/' + g.user.office[0:3] + '/sdc')
    
    if g.user.region:
        return redirect('/consolidated/' + g.user.region + '/sdc')

    return redirect('/consolidated')    


@app.route('/logout', methods=['GET'])
def logout():
    g.user = None
    session.pop('openid', None)
    return redirect('/login')


@oid.require_login
@app.route('/consolidated', methods=['POST','GET'])
def consolidated(): 
    if request.method == 'POST':
        option = request.form.get('target')

        if option == "Dashboard":
            return redirect('/dashboard/conf')

        office = request.form.get('office')
        page = request.form.get('page')

        office = escape(office)
        page = escape(page)

        return redirect('/consolidated/' + str(office)[0:3] + '/' + page)

    if g.user.rank in [None, 'Intern']:
        offices =  Location.query.filter_by(region=g.user.region).group_by(Location.locationname).order_by(asc(Location.locationname)).with_entities(Location.locationname).all()
    
    else:
        offices = Location.query.group_by(Location.locationname).order_by(asc(Location.locationname)).with_entities(Location.locationname).all()

    return render_template('index.html', offices=offices)


@oid.require_login
@app.route('/consolidated/<office>/<page>', methods=['GET', 'POST'])
def office(office, page):
    date = datetime.today().strftime('%Y-%m-%d')

    office = escape(office)
    page = escape(page)
    
    if g.user.rank in [None, 'Intern']:
        locations = Location.query.filter(Location.locationname.like(office + '%'), Location.region == g.user.region).all()
    else:
        locations = Location.query.filter(Location.locationname.like(office + '%')).all()

    if not locations:
        return redirect('/consolidated')

    location_ids = list(map(lambda l: l.locationid, locations))

    shifts = Shift.query.filter(Shift.is_active == True, Shift.shift_location.in_(location_ids)).order_by(asc(Shift.time), asc(Shift.person)).all()

    all_shifts = []
    extra_shifts = []
    in_shifts = []
    shift_ids = []
    
    for shift in shifts:
        shift_ids.append(shift.id)
        if shift.status in ['Completed', 'Declined', 'No Show', 'Resched']:
            extra_shifts.append(shift)
        elif shift.status == 'In':
            in_shifts.append(shift)
        else: 
            all_shifts.append(shift)

    all_shifts.extend(in_shifts)
    all_shifts.extend(extra_shifts)
        
    groups = CanvassGroup.query.join(CanvassGroup.canvass_shifts).options(contains_eager(CanvassGroup.canvass_shifts)).filter(CanvassGroup.is_active==True, Shift.id.in_(shift_ids)).order_by(asc(CanvassGroup.check_in_time)).all()

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

        try: 
            sync_shifts = SyncShift.query.filter(SyncShift.locationname.like(office + '%'), SyncShift.startdate==date).all()

            for shift in all_shifts:
                if shift.volunteer.van_id == None or shift.shift_flipped:
                    continue

                sync = next((x for x in list(sync_shifts) if (x.vanid == shift.volunteer.van_id and x.starttime == shift.time and x.eventtype == shift.eventtype)), None)
                
                if not sync:
                    continue
                
                if sync.status != shift.status and shift.status in ['Completed', 'Declined', 'No Show', 'Resched']:
                    if shift.status in ['Completed', 'Resched'] or not sync.status == 'Invited':
                        review_shifts.append(shift)
        except:
            print('Sync shifts is running')
        
        return render_template('review.html', active_tab=page, header_stats=header_stats, office=office, stats=stats, shifts=review_shifts)

    else:
        return redirect('/consolidated/' + office + '/sdc')

@oid.require_login
@app.route('/consolidated/<office>/<page>/pass', methods=['POST'])
def add_pass(office, page):
    keys = list(request.form.keys())
    parent_id = request.form.get('parent_id')
    page_load_time = datetime.strptime(urllib.parse.unquote(request.form.get('page_load_time')), '%I:%M %p').time()

    if not parent_id or not parent_id.isdigit():
        return abort(400)

    return_var = None

    if page == 'kph':
        if 'claim' in keys:
            group = CanvassGroup.query.options(joinedload(CanvassGroup.claim_user)).get(parent_id)
        else:
            group = CanvassGroup.query.options(joinedload(CanvassGroup.canvass_shifts)).get(parent_id)

        if not group or not group.is_active:
            return Response('Group Not Found', status=400)

        if group.updated_by_other(page_load_time, g.user):
            return Response('This Canvass Group has been updated by a different user since you last loaded the page. Please refresh and try again.', 400)
        
        if 'claim' in keys:
            if group.claim:
                if group.claim != g.user.id:
                    return Response('Another user has claimed this group', 400)

                group.claim = None
                return_var = jsonify({
                    'name': 'Claim',
                    'color': None
                })
            else:
                group.claim = g.user.id
                return_var = jsonify({
                    'name': g.user.claim_name(),
                    'color': g.user.color
                })
                
        else:
            if 'shift_id[]' in keys:
                shift_ids = request.form.getlist('shift_id[]')

                for id in shift_ids:
                    if not id.isdigit():
                        return Response('Invalid shift id', status=400)

                shifts = group.update_shifts(shift_ids, g.user)
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

            elif 'out' in keys:
                group = group.setOut()

                return_var  = jsonify({
                    'is_returned': group.is_returned,
                    'departure': group.departure.strftime('%I:%M %p'), 
                    'check_in_time': group.check_in_time.strftime('%I:%M %p') if group.check_in_time else '',
                    'last_check_in': group.last_check_in.strftime('%I:%M %p'),
                    'check_ins': group.check_ins
                })

            elif 'actual' in keys:
                check_in_amount = request.form.get('actual')

                if check_in_amount and not check_in_amount.isdigit():
                    return Response('Check In Amount must be a number"', status=400)

                group = group.check_in(check_in_amount)

                note = group.add_note('kph', check_in_amount + " doors", g.user)

                return_var = jsonify({
                    'check_in_time': (group.check_in_time.strftime('%I:%M %p') if group.check_in_time else None), 
                    'last_check_in': (group.last_check_in.strftime('%I:%M %p') if group.last_check_in else None),
                    'check_ins': group.check_ins,
                    'actual': group.actual,
                    'note': note, 
                    'is_returned': group.is_returned
                })

            elif 'departure' in keys:
                new_departure_time = request.form.get('departure')
                
                try:
                    new_departure_time = parse(new_departure_time)
                except:
                    return Response('Invalid Time', 400)

                group = group.change_departure(new_departure_time)

                note = group.add_note('kph', 'Departure changed to ' + group.departure.strftime('%I:%M %p'), g.user)

                return_var = jsonify({
                    'check_in_time': group.check_in_time.strftime('%I:%M %p'), 
                    'last_check_in': group.last_check_in.strftime('%I:%M %p'),
                    'check_ins': group.check_ins,
                    'actual': group.actual,
                    'note': note
                })


            elif 'note' in keys:
                note_text = request.form.get('note')

                note_text = escape(note_text)

                return_var = group.add_note(page, note_text, g.user)
                
            elif 'cellphone' in keys and 'vol_id' in keys:
                cellphone = request.form.get('cellphone')

                phone_sanitized = re.sub('[- ().+]', '', cellphone)

                if phone_sanitized and not phone_sanitized.isdigit():
                    return Response('Invalid Phone', status=400)

                vol_id = request.form.get('vol_id')
                volunteer = Volunteer.query.get(vol_id)

                if not volunteer:
                    return Response('Could not find volunteer', status=400)

                if volunteer.updated_by_other(page_load_time, g.user):
                    return Response('This volunteer has been updated by another user since you last loaded the page. Please refresh and try again.', 400)

                volunteer.cellphone = phone_sanitized
                volunteer.last_user = g.user.id
                volunteer.last_update = datetime.now().time()
            
            elif 'goal' in keys: 
                goal = request.form.get('goal')

                if goal and not goal.isdigit():
                    return Response('"Goal" must be a number"', status=400)
                group.goal = int(goal)

            elif 'packets_given' in keys:
                packets_given = request.form.get('packets_given')
                if packets_given and not packets_given.isdigit():
                    return Response('"packets_given" must be a number"', status=400)

                group.packets_given = int(packets_given)

            elif 'packet_names' in keys:
                packet_names = request.form.get('packet_names')
                packet_names = escape(packet_names)

                group.packet_names = packet_names

            
            group.last_update = datetime.now().time()
            group.last_user = g.user.id

    else: 
        shift = Shift.query.get(parent_id)

        if not shift or not shift.is_active:
            return Response('Shift not found', status=400)
        
        if shift.updated_by_other(page_load_time, g.user):
            return Response('This Shift has been updated by a different user since you last loaded the page. Please refresh and try again.', 400)
        
        if 'claim' in keys:
            if shift.claim:
                if shift.claim != g.user.id:
                    return Response('Another user has claimed this shift', 400)

                shift.claim = None
                return_var = jsonify({
                    'name': 'Claim',
                    'color': None
                })
            else:
                shift.claim = g.user.id
                return_var = jsonify({
                    'name': g.user.claim_name(),
                    'color': g.user.color
                })

        else:
            if 'status' in keys:
                status = request.form.get('status')
                status = escape(status)

                if not status in ['Completed', 'Declined', 'No Show', 'Resched', 'Same Day Confirmed', 'In', 'Scheduled', 'Invited', 'Left Message']:
                    return Response('Invalid status', status=400)

                return_var = shift.flip(page, status, g.user)    

            elif 'first_name' in keys:
                first = request.form.get('first_name')

                if shift.volunteer.updated_by_other(page_load_time, g.user):
                    return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

                first = escape(first)
                shift.volunteer.first_name = first 

            elif 'last_name' in keys:
                last = request.form.get('last_name')

                if shift.volunteer.updated_by_other(page_load_time, g.user):
                    return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

                last = escape(last)
                shift.volunteer.last_name = last 

            elif 'vanid' in keys:
                if shift.volunteer.updated_by_other(page_load_time, g.user):
                    return Response('This volunteer has been updated by another user since you last loaded the page. Please refresh and try again.', 400)

                vanid = request.form.get('vanid')
                    
                if vanid and not vanid.isdigit():
                    return Response('Invalid VanID', 400)
                
                if vanid:
                    volunteer = Volunteer.query.filter_by(van_id=vanid).first()

                    if volunteer:
                        shift.volunteer = volunteer
                        shift.person = volunteer.id
                    else:
                        shift.volunteer.van_id = vanid
                        
                        try: 
                            next_shift = SyncShift.query.filter(SyncShift.vanid==vanid, datetime.now().date() < SyncShift.startdate).order_by(SyncShift.startdate).first()
                        except:
                            return Response('Could not update VanID at this time, please try again in a few minutes', 400)
                            
                        if next_shift:
                            shift.volunteer.next_shift = next_shift.startdate
                        
                            if next_shift.status == 'Confirmed':
                                shift.volunteer.next_shift_confirmed = True
                        else:
                            shift.volunteer.next_shift = None
                            shift.volunteer.next_shift_confirmed = False
            
            elif 'phone' in keys:
                phone = request.form.get('phone')

                if shift.volunteer.updated_by_other(page_load_time, g.user):
                    return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

                phone_sanitized = re.sub('[- ().+]', '', phone)

                if phone_sanitized and not phone_sanitized.isdigit():
                    return Response('Invalid Phone', status=400)
                
                shift.volunteer.phone_number = phone_sanitized 

            elif 'cellphone' in keys:
                cellphone = request.form.get('cellphone')
                
                if shift.volunteer.updated_by_other(page_load_time, g.user):
                    return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

                phone_sanitized = re.sub('[- ().+]', '', cellphone)

                if phone_sanitized and not phone_sanitized.isdigit():
                    return Response('Invalid Phone', status=400)

                shift.volunteer.cellphone = phone_sanitized
                shift.volunteer.last_user = g.user.id
                shift.volunteer.last_update = datetime.now().time()

            elif 'note' in keys:
                note_text = request.form.get('note')

                note_text = escape(note_text)

                return_var = shift.add_note(page, note_text, g.user)

            elif 'passes' in keys:
                return_var = str(shift.add_pass(page))
            
            
            shift.last_update = datetime.now().time()
            shift.last_user = g.user.id

    db.session.commit()

    return return_var if return_var else ''


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

    group.update_shifts(shift_ids, g.user)

    if goal:
        if not goal.isdigit():
            return abort(400, 'Goal must be a number')
        
        group.goal = int(goal)
    
    if packets_given:
        if not packets_given.isdigit():
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

    shift_ids = request.form.getlist('shift_id[]')
    success = vanservice.sync_shifts(shift_ids)

    if success:
        return redirect('/consolidated/' + office + '/review')
    else: 
        return Response('The remaining shifts could not be found. Please flip them manually in VAN.', 400)

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
    page = escape(page)

    locations = Location.query.filter(Location.locationname.like(office + '%')).all()

    if not locations:
        return Response('Locations not found', 400)

    location_ids = list(map(lambda l: l.locationid, locations))

    updates = []

    if page == 'kph':
        all_groups = CanvassGroup.query.join(CanvassGroup.canvass_shifts).filter(CanvassGroup.is_active==True, Shift.shift_location.in_(location_ids)).all()

        for gr in all_groups:
            updates.append({
                'id': gr.id,
                'updated': gr.updated_by_other(page_load_time, g.user),
                'name': gr.claim_user.claim_name() if gr.claim else 'Claim',
                'color': gr.claim_user.color if gr.claim else None
            })

    else:
        shifts = Shift.query.filter(Shift.is_active == True, Shift.shift_location.in_(location_ids)).all()
        
        for shift in shifts:
            updates.append({
                'id': shift.id,
                'updated': shift.updated_by_other(page_load_time, g.user),
                'name': shift.claim_user.claim_name() if shift.claim else 'Claim',
                'color': shift.claim_user.color if shift.claim else None
            })

    return jsonify(updates)

@oid.require_login
@app.route('/consolidated/<office>/<page>/delete_element', methods=['DELETE'])
def delete_element(office, page):
    parent_id = request.form.get('parent_id')
    name = ''

    if page == 'kph':
        group = CanvassGroup.query.options(joinedload(CanvassGroup.canvass_shifts)).get(parent_id)
        group.is_active = False
        group.last_user = g.user.id
        group.last_update = datetime.now().time()
        name = ','.join(list(map(lambda s: s.volunteer.first_name + ' ' + s.volunteer.last_name, group.canvass_shifts)))
    
    else: 
        shift = Shift.query.get(parent_id)

        if shift.canvass_group:
            if shift.group.is_active:
                return Response('Please delete shift from canvass group first', 400)
        
        shift.is_active = False
        shift.last_user = g.user.id
        shift.last_update = datetime.now().time()
        name = shift.volunteer.first_name + ' ' + shift.volunteer.last_name

    db.session.commit()
    return name

@oid.require_login
@app.route('/consolidated/<office>/<page>/delete_note', methods=['DELETE'])
def delete_note(office, page):
    shift_id = request.form.get('shift_id')
    text = request.form.get('text')
    print(shift_id, text)

    page = escape(page)

    note = Note.query.filter_by(type=page, text=text, note_shift=shift_id).first()
    db.session.delete(note)
    db.session.commit()

    return ''

@oid.require_login
@app.route('/user', methods=['GET', 'POST'])
def user():
    if g.user.rank in [None, 'Intern']:
        offices =  Location.query.filter_by(region=g.user.region).group_by(Location.locationname).order_by(asc(Location.locationname)).with_entities(Location.locationname).all()
    
    else:
        offices = Location.query.group_by(Location.locationname).order_by(asc(Location.locationname)).with_entities(Location.locationname).all()

    if request.method == "POST":
        user = User.query.get(g.user.id)
        keys = request.form.keys()

        if 'firstname' in keys:
            firstname = request.form.get('firstname')

            firstname = escape(firstname)
            user.firstname = firstname

        if 'lastname' in keys:
            lastname = request.form.get('lastname')
            lastname = escape(lastname)
            user.lastname = lastname


        if 'fullname' in keys:
            fullname = request.form.get('fullname')
            fullname = escape(fullname)
            user.fullname = fullname

        if 'color' in keys:
            color = request.form.get('color')

            if color[0] == '#':
                color = color[1:]

            if not color.isalnum():
                return Response('Color must be numbers and letters only', 400)
            
            user.color = color

        office = request.form.get('office')

        office = escape(office)
        user.office = office

        db.session.commit()

    return render_template('user.html', offices=offices)


@oid.require_login
@app.route('/help')
def help():
    return render_template('help.html')


@oid.require_login
@app.route('/consolidated/<office>/<page>/backup')
def backup(office, page):
    office = escape(office)
    page = escape(page)

    locations = Location.query.filter(Location.locationname.like(office + '%')).all()

    if not locations:
        return redirect('/consolidated')

    location_ids = list(map(lambda l: l.locationid, locations))

    if page == 'kph':
        groups = BackupGroup.query.join(BackupGroup.canvass_shifts).options(contains_eager(BackupGroup.canvass_shifts)).filter(BackupShift.shift_location.in_(location_ids), BackupShift.date > (datetime.today() - timedelta(days=7)).date()).order_by(desc(BackupGroup.id)).all()

        return render_template('backups.html', groups=groups)

    else: 
        shifts = BackupShift.query.filter(BackupShift.shift_location.in_(location_ids), BackupShift.date > (datetime.today() - timedelta(days=7)).date()).order_by(desc(BackupShift.id)).all()

        return render_template('backups.html', shifts=shifts)


@oid.require_login
@app.route('/consolidated/<office>/<page>/confirm_shift', methods=['POST'])
def confirm_shift(office, page):
    vanid = request.form.get('vanid')

    if not vanid:
        return Response('No vanid found', 400)

    if not vanid.isdigit():
        return Response('Invalid vanid', 400)

    date_str = urllib.parse.unquote(request.form.get('date'))
    
    date = datetime.strptime(date_str, '%m/%d %I:%M %p').replace(year=2018)

    if date > (datetime.today() + timedelta(days=4)):
        return Response('Shift too far out', 400)

    success = vanservice.confirm_shift(vanid, date)

    if success == True:
        return Response('Success', 200)
    else:
        return Response('Failed to update shift for ' + vanid, 400)


@oid.require_login
@app.route('/consolidated/<office>/<page>/future_shifts', methods=['GET'])
def get_future_shifts(office, page):
    vanid = request.args.get('vanid')

    if not vanid:
        return Response('No vanid found', 400)

    if not vanid.isdigit():
        return Response('Invalid vanid', 400)

    try: 
        future_shifts = SyncShift.query.filter(SyncShift.vanid == vanid, SyncShift.startdate > datetime.today().date()).order_by(SyncShift.startdate).all()
    except:
        return Response('Could not get future shifts at this time, please check back in a few minutes', 400)

    return jsonify(list(map(lambda x: x.serialize(), future_shifts)))


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
