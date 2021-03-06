from flask import flash, g, redirect, render_template, \
    request, session, jsonify, json, Response, send_from_directory
from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy.sql import func
from flask_socketio import send, emit, join_room, leave_room, disconnect
from datetime import datetime, timedelta
from dateutil.parser import parse
from utility import str_sanitize

import re
import urllib
import os
import functools
import time

from models import db, Volunteer, Location, Shift, Note, User, ShiftStats, \
    CanvassGroup, HeaderStats, SyncShift, BackupGroup, BackupShift
from models.dashboard_totals import DashboardTotal
from setup_config import ranks, regions
from services import PassService, SocketIoService, VanService

from app import app, oid, schema, socketio

try:
    vanservice = VanService()
except:
    print('Vanservice does not have environment variables')

oid.init_app(app)

'''
This wrapper is only for the web sockets endpoints because the @login_required
decorator doesn't work as per the docs; Also, the before_request handlers do not run
for socket events, so the code that populates g does not get a chance to run, as documented
See: https://flask-socketio.readthedocs.io/en/latest/
'''
def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        
        if 'openid' in session:
            g.user = User.query.filter(User.openid==session['openid']).first()
            
            if g.user is None or not g.user.is_allowed:
                disconnect()
            else:
                return f(*args, **kwargs)
        else:
            disconnect()
    return wrapped

@app.before_request
def logout_before():
    
    if request.path.startswith('/static') or request.path.startswith('/favicon') or request.path.startswith('/loaderio-cb6afdec0447c3b6ec9bce41757c581c'):
        return
    if request.path.startswith('/oidc_callback'):
        return

    g.time_now = datetime.now().time()

    g.user = None
    redir = False
    if 'openid' in session:
        g.user = User.query.filter(User.openid==session['openid']).first()

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

    if g.user.rank in ['Intern', 'DFO', 'FO'] and g.user.office and g.user.office != 'N/A':
            return redirect('/consolidated/' + g.user.office[0:3] + '/sdc')
    
    if g.user.region and g.user.rank == 'FD':
        if g.user.region == 'HQ':
            return redirect('/dashboard/top')

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

        office = str_sanitize(office)
        page = str_sanitize(page)

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

    office = str_sanitize(office)
    page = str_sanitize(page)
    
    if g.user.rank in [None, 'Intern']:
        locations = Location.query.filter(Location.locationname.like(office + '%'), Location.region == g.user.region).all()
    else:
        locations = Location.query.filter(Location.locationname.like(office + '%')).all()

    if not locations:
        return redirect('/consolidated')

    location_ids = list(map(lambda l: l.locationid, locations))

    if page == 'kph':
        shifts = Shift.query.options(joinedload(Shift.group)).filter(Shift.is_active == True, Shift.shift_location.in_(location_ids)).order_by(asc(Shift.time), asc(Shift.person)).all()
    else:
        shifts = Shift.query.filter(Shift.is_active == True, Shift.shift_location.in_(location_ids)).order_by(asc(Shift.time), asc(Shift.person)).all()

    all_shifts = []
    extra_shifts = []
    in_shifts = []
    group_ids = []
    
    for shift in shifts:
        if shift.canvass_group:
            group_ids.append(shift.canvass_group)

        if shift.status in ['Completed', 'Declined', 'No Show', 'Resched']:
            extra_shifts.append(shift)
        elif shift.status == 'In':
            in_shifts.append(shift)
        else: 
            all_shifts.append(shift)

    all_shifts.extend(in_shifts)
    all_shifts.extend(extra_shifts)

    if page == 'kph':
        groups = CanvassGroup.query.options(joinedload(CanvassGroup.canvass_shifts)).filter(CanvassGroup.is_active==True, CanvassGroup.id.in_(group_ids)).order_by(asc(CanvassGroup.check_in_time)).all()
    
    else:
        groups = CanvassGroup.query.filter(CanvassGroup.is_active==True, CanvassGroup.id.in_(group_ids)).all()

    header_stats = HeaderStats(all_shifts, groups)

    if page == 'sdc':
        return render_template('same_day_confirms.html', active_tab=page, header_stats=header_stats, office=office, \
                 shifts=all_shifts)

    elif page == 'kph':
        return render_template('kph.html', active_tab=page, header_stats=header_stats, office=office, shifts=all_shifts, \
                 groups=groups)

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
    passservice = PassService()
    return passservice.add_pass(office, page)


@oid.require_login
@app.route('/consolidated/<office>/<page>/add_group', methods=['POST'])
def add_group(office, page):
    group = CanvassGroup(g.user.id)

    shift_ids = request.form.getlist('shift_id[]')
    goal = request.form.get('goal')
    packets_given = request.form.get('packets_given')
    packet_names = request.form.get('packet_names')

    for id in shift_ids:
        if not id.isdigit():
            return Response('Invalid shift id', 400)

    res = group.update_shifts(shift_ids, g.user)

    if isinstance(res, str):
        return Response(res, 400)

    if goal:
        if not goal.isdigit():
            return Response('Goal must be a number', 400)
        
        group.goal = int(goal)
    
    if packets_given:
        if not packets_given.isdigit():
            return Response('# of Packets must be a number', 400)

        group.packets_given = int(packets_given)

    if packet_names:
        packet_names = str_sanitize(packet_names)
        
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
        firstname = str_sanitize(firstname)

    if lastname: 
        lastname = str_sanitize(lastname)

    if phone:
        phone_sanitized = re.sub('[- ().+]', '', phone)

        if not phone_sanitized.isdigit():
            return Response('Invalid Phone', 400)
        
    if time and not time in ['10:00 AM', '1:00 PM', '4:00 PM', '6:00 PM']:
        return Response('Invalid time', 400)

    if role and not role in ['Canvassing', 'Phonebanking', 'Comfort Vol', 'Intern Onboarding', 'Intern Interview']:
        return Response('Invalid activity', 400)

    eventtype = "Volunteer DVC" if role in ['Canvassing', 'Phonebanking'] else role

    office = str_sanitize(office)
    location = Location.query.filter(Location.locationname.like(office + '%')).first()

    shift = Shift(eventtype, time, datetime.now().date(), 'In', role, None, location.locationid, g.user.id)

    vol = Volunteer.query.filter_by(first_name=firstname, last_name=lastname, phone_number=phone_sanitized).order_by(Volunteer.van_id).first()

    if not vol:
        vol = Volunteer(None, firstname, lastname, phone_sanitized, None)
        db.session.add(vol)
        db.session.commit()

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


@socketio.on('join', namespace='/live-updates')
@authenticated_only
def on_join(data):
    print('received WS message!!! ' + str(data))
    socketIoService = SocketIoService()
    room = socketIoService.room_name(str_sanitize(data['office']), str_sanitize(data['page']))

    join_room(room)
    
    join_room('broadcast')

    
@socketio.on('view', namespace='/live-updates')
@authenticated_only
def on_view(data):
    if 'office' in data and 'page' in data:
        office = str_sanitize(data['office'])
        page = str_sanitize(data['page'])
    
        # Broadcast the viewers that are looking at this page (the relevant office)
        # User ID, name, and color are passed to show the users that are in 
        # Note that time.time() is the UNIX timestamp
        json = { 'user_id': g.user.id, 'user_color': g.user.color, 'user_short_name': g.user.claim_name(), \
                 'viewed_at': int(time.time()) }

        socektIoService = SocketIoService()
        socektIoService.emit_update('viewers', office, page, json)


@oid.require_login
@app.route('/consolidated/<office>/<page>/delete_element', methods=['DELETE'])
def delete_element(office, page):
    parent_id = request.form.get('parent_id')
    name = ''

    if page == 'kph':
        group = CanvassGroup.query.get(parent_id)
        group.is_active = False
        group.last_user = g.user.id
        group.last_update = datetime.now().time()
        name = 'canvass group'
    
    else: 
        shift = Shift.query.options(joinedload(Shift.group)).get(parent_id)

        if shift.canvass_group and shift.group.is_active:
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

    page = str_sanitize(page)

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

            firstname = str_sanitize(firstname)
            user.firstname = firstname

        if 'lastname' in keys:
            lastname = request.form.get('lastname')
            lastname = str_sanitize(lastname)
            user.lastname = lastname


        if 'fullname' in keys:
            fullname = request.form.get('fullname')
            fullname = str_sanitize(fullname)
            user.fullname = fullname

        if 'color' in keys:
            color = request.form.get('color')

            if color[0] == '#':
                color = color[1:]

            if not color.isalnum():
                return Response('Color must be numbers and letters only', 400)
            
            user.color = color

        office = request.form.get('office')

        if office and office != 'None' and not office in list(map(lambda x: x.locationname, offices)):
            return Response('Invalid Office', 400)
        
        if office == "None":
            office = None

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
    office = str_sanitize(office)
    page = str_sanitize(page)

    locations = Location.query.filter(Location.locationname.like(office + '%')).all()

    if not locations:
        return redirect('/consolidated')

    location_ids = list(map(lambda l: l.locationid, locations))

    if page == 'kph':
        groups = BackupGroup.query.join(BackupGroup.canvass_shifts).options(contains_eager(BackupGroup.canvass_shifts)).filter(BackupShift.shift_location.in_(location_ids)).order_by(desc(BackupGroup.id)).all()

        return render_template('backups.html', groups=groups)

    else: 
        shifts = BackupShift.query.filter(BackupShift.shift_location.in_(location_ids)).order_by(desc(BackupShift.id)).all()

        return render_template('backups.html', shifts=shifts)


@oid.require_login
@app.route('/consolidated/<office>/<page>/confirm_shift', methods=['POST'])
def confirm_shift(office, page):
    if not g.user.rank in ['DATA', 'FD', 'FO', 'DFO']:
        return Response('You do not have access to confirm future shifts. Please ask paid staffer to do this.', 400)
        
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
@app.route('/consolidated/<office>/<page>/future_shifts', methods=['POST'])
def get_future_shifts(office, page):
    vol_ids = request.form.getlist('vol_ids[]')

    if not vol_ids:
        return Response('No vol_id found', 400)

    vol_ids = list(x for x in vol_ids if x.isdigit())

    volunteers = Volunteer.query.filter(Volunteer.id.in_(vol_ids)).all()

    vanids = list(x.van_id for x in volunteers if x.van_id)

    try: 
        future_shifts = SyncShift.query.filter(SyncShift.vanid.in_(vanids), SyncShift.startdate > datetime.today().date()).order_by(SyncShift.startdate).all()
    except:
        return Response('Could not get future shifts at this time, please check back in a few minutes', 400)

    return jsonify({
        'vols': list(map(lambda x: x.serialize(), volunteers)),
        'shifts': list(map(lambda x: x.serialize(), future_shifts))
    })

@oid.require_login
@app.route('/consolidated/<office>/<page>/vol_pitch', methods=['POST'])
def update_vol_pitch(office, page):
    vol_id = request.form.get('vol_id')

    if not vol_id:
        return Response('No vol id', 400)
    
    
    if not vol_id.isdigit():
        return Response('Invalid vol id', 400)

    vol = Volunteer.query.get(vol_id)

    if not vol:
        return Response('Volunteer could not be found.', 400)

    has_pitched_today = request.form.get('has_pitched_today')
    
    vol.has_pitched_today = True if has_pitched_today == 'True' else False

    extra_shifts_sched = request.form.get('extra_shifts_sched')

    if extra_shifts_sched and not extra_shifts_sched.isdigit():
        return Response('Extra shifts must be a number', 400)

    vol.extra_shifts_sched = extra_shifts_sched if extra_shifts_sched else None

    db.session.commit()

    return Response('success', 200)


@app.route('/loaderio-cb6afdec0447c3b6ec9bce41757c581c/')
def loader_io():
    return app.send_static_file('loaderio-cb6afdec0447c3b6ec9bce41757c581c.txt')

@oid.require_login
@app.route('/users', methods=['POST', 'GET'])
def display_users():
    if request.method == "POST":
        id = request.form.get('id')

        if id.isdigit():
            user = User.query.get(id)
        else:
            return Response('Invalid User Id', 400)
        
        if g.user.rank == 'DATA':
            rank = request.form.get('rank').strip()
            
            if rank in ranks and user.rank != rank:
                user.rank = rank
            
            region = request.form.get('region')
            
            if region in regions and user.region != region:
                user.region = region
            
            allowed = request.form.get('allowed')
            
            allowed = True if allowed == 'on' else False
            
            if user.is_allowed != allowed:
                user.is_allowed = allowed
            
        office = request.form.get('office')

        if office:
            if g.user.rank=='DATA':
                office = Location.query.filter(Location.locationname.like(office[0:3] + '%')).first()
            elif g.user.rank=='FD':
                office = Location.query.filter(Location.locationname.like(office[0:3] + '%'), Location.region==g.user.region).first()
            else:
                return redirect('/users')
        
        if office:
            office = office.locationname

        if user.office != office:
            user.office = office
        
        db.session.add(user)
        db.session.commit()

    if g.user.rank == 'DATA' or g.user.region == 'HQ':
        all_users = db.session.query(User.id,
                                     User.email, 
                                     User.rank, 
                                     User.region, 
                                     User.office, 
                                     User.is_allowed,
                                     User.firstname,
                                     User.lastname, 
                                     func.min(Note.time).label('first_active'), 
                                     func.max(Note.time).label('most_recent')
                                     ).join(Note, User.id==Note.user_id, isouter=True
                                     ).group_by(User.id, User.email, User.region, User.office
                                     ).order_by(asc(User.region), asc(User.office)
                                     ).all()
        locations = Location.query.order_by(Location.locationname.asc()).all()
    elif g.user.rank == 'FD':
        all_users = db.session.query(User.id, 
                                    User.email, 
                                    User.rank, 
                                    User.region, 
                                    User.office, 
                                    User.is_allowed, 
                                    User.firstname,
                                    User.lastname,
                                    func.min(Note.time).label('first_active'), 
                                    func.max(Note.time).label('most_recent')
                                    ).join(Note, User.id==Note.user_id, isouter=True
                                    ).filter(User.region==g.user.region
                                    ).group_by(User.id, User.email, User.region, User.office
                                    ).order_by(asc(User.region), asc(User.office)
                                    ).all()
        locations = Location.query.filter_by(region=g.user.region).order_by(Location.locationname.asc()).all()

    else:
        return redirect('/consolidated')
        
    return render_template('users.html', all_users=all_users, locations=locations, user=g.user, ranks=ranks, regions=regions)

@oid.require_login
@app.route('/users/add_user', methods = ['POST'])
def add_user():
    if request.method == 'POST':

        email = request.form.get('email').strip()
        rank = request.form.get('rank')
        region = request.form.get('region')
        office = request.form.get('office')
        firstname = str_sanitize(request.form.get('firstname'))
        lastname = str_sanitize(request.form.get('lastname'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return Response('Invalid Email', 400)

        user = User.query.filter_by(email=email).first()
        if not user:

            if firstname == '':
                firstname = None
            
            if lastname == '':
                lastname = None

            if not region in regions or (g.user.rank != 'DATA' and g.user.region != 'HQ' and region != g.user.region):
                return Response('Invalid Region', 400)

            if g.user.rank == "DATA":
                is_allowed = True
            else:
                is_allowed = False

            if g.user.rank != 'DATA' and rank not in ['Intern','DFO','FO']:
                rank = 'FO'

            office = Location.query.filter(Location.locationname.like(office[0:3] + '%')).first()
            office = office.locationname if office else None

            user = User(email=email, rank=rank, region=region, office=office, is_allowed=is_allowed, firstname=firstname, lastname=lastname)
            db.session.add(user)
            db.session.commit()

        else:
            return Response('User already exists', 400)

    return redirect('/users')

@oid.require_login
@app.route('/consolidated/volunteer_history/<vol_id>', methods=['GET', 'POST'])
def see_volunteer_history(vol_id):
    if not vol_id:
        return Response('No volunteer id', 500)
    
    if not vol_id.isdigit():
        return Response('Invalid volunteer id', 500)

    volunteer = Volunteer.query.get(vol_id)

    if not volunteer:
        return Response('Volunteer not found', 404)

    if request.method == 'POST':

        # VanID
        van_id = request.form.get('vanid')

        if van_id and not van_id.isdigit():
            return Response('Invalid VanID', 400)

        volunteer.van_id = van_id

        # first name
        first_name = str_sanitize(request.form.get('firstname'))
        volunteer.first_name = first_name

        # last name
        last_name = str_sanitize(request.form.get('lastname'))
        volunteer.last_name = last_name

        # phone
        phone_number = request.form.get('phone')
        phone_sanitized = re.sub('[- ().+]', '', phone_number)

        if phone_sanitized and not phone_sanitized.isdigit():
            return Response('Invalid Phone', status=400)

        volunteer.phone_number = phone_sanitized

        # cellphone
        cellphone = request.form.get('cellphone')
        cellphone_sanitized = re.sub('[- ().+]', '', cellphone)

        if cellphone_sanitized and not cellphone_sanitized.isdigit():
            return Response('Invalid Cell Phone', status=400)

        volunteer.cellphone = cellphone_sanitized

        db.session.commit()

    past_shifts = BackupShift.query.join(BackupShift.volunteer).filter(Volunteer.id == vol_id).all()

    future_shifts = None
    if volunteer.van_id:
        future_shifts = SyncShift.query.filter(SyncShift.vanid == volunteer.van_id, SyncShift.startdate > datetime.today().date()).order_by(SyncShift.startdate).all()

    past_groups = BackupGroup.query.join(BackupGroup.canvass_shifts).join(BackupShift.volunteer).options(contains_eager(BackupGroup.canvass_shifts)).filter(Volunteer.id == vol_id).all()
    
    return render_template('volunteer.html', volunteer=volunteer, past_shifts=past_shifts, future_shifts=future_shifts, past_groups=past_groups)

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/consolidated')

@app.errorhandler(500)
def internal_service_error(e):
    if request.endpoint == 'pass':
        return Response('Internal Service Error', 500)

    return redirect('/consolidated')

if __name__ == "__main__":
    socketio.run(app, debug=True)
