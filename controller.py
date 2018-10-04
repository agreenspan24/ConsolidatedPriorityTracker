from datetime import datetime

from flask import flash, g, redirect, render_template, request, session, abort

from sqlalchemy import and_, asc

from app import app, oid
from config import settings
##from cptvanapi import CPTVANAPI
from models import db, Volunteer, Location, Shift, Note, User, ShiftStats, CanvassGroup
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

        print(option)
        if option == "Dashboard":
            return redirect('/dashboard')

        office = request.form.get('office')
        page = request.form.get('page')
        return redirect('/consolidated/' + str(office)[0:3] + '/' + page)

    user = User.query.filter_by(email=g.user.email).first()
    dashboard_permission = user.rank == 'DATA' or user.rank == 'FD'

    return render_template('index.html', user=g.user, offices=offices, show_dashboard=dashboard_permission)

@oid.require_login
@app.route('/consolidated/<office>/<page>', methods=['GET', 'POST'])
def office(office, page):
    date = datetime.today().strftime('%Y-%m-%d')

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
    try:
        parent_id = request.form.get('parent_id')
        note_text = request.form.get('note')
        cellphone = request.form.get('cellphone')
        van_id = request.form.get('van_id')

        if page == 'kph':
            returned = request.form.get('returned')
            checked_in = request.form.get('checked_in')

            if parent_id:
                group = CanvassGroup.query.get(group_id)

                if returned:
                    CanvassGroup.returned()

                if checked_in:
                    group = CanvassGroup.check_in()

                if note_text:
                    CanvassGroup.add_note(page, note_text)
                
                if cellphone:
                    volunteer = Volunteer.query.filter_by(van_id=van_id).first()
                    volunteer.cellphone = cellphone
                
                db.session.commit()
                return group
        else: 
            status = request.form.get('status')
            return_var = ""
            if status:
                shift = Shift.query.get(parent_id)
                shift.flip(status)     

            if note_text:
                shift = Shift.query.get(parent_id)
                return_var = shift.add_call_pass(page, note_text)

            if cellphone:
                volunteer = Volunteer.query.filter_by(van_id=van_id).first()
                volunteer.cellphone = cellphone

            db.session.commit()
            return return_var
    except:
        abort(500)

@oid.require_login
@app.route('/consolidated/<office>/<page>/add_group', methods=['POST'])
def add_group(office, page):
    try:
        group = CanvassGroup()

        shift_ids = request.form.getlist('shift_id[]')

        print(shift_ids, group.departure)

        if not shift_ids:
            abort(404)

        CanvassGroup.add_shifts(shift_ids)

        goal = request.form.get('goal')
        if goal:
            group.goal = goal

        packets_given = request.form.get('packets_given')
        if packets_given: 
            group.packets_given = int(packets_given)

        packet_names = request.form.get('packet_names')
        if packet_names:
            group.packet_names = request.form.get('packet_names')
        
        db.session.add(group)
        db.session.commit()

        return redirect('/consolidated/' + office + '/kph')
    except:
        abort(500)

@oid.require_login
@app.route('/consolidated/<office>/<page>/walk_in', methods=['POST'])
def add_walk_in(office, page):
    try:
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone = request.form.get('phone')
        time = request.form.get('time')
        role = request.form.get('activity')

        eventtype = "Volunteer DVC" if role in ['Canvassing', 'Phonebanking'] else role

        location = Location.query.filter(Location.locationname.like(office + '%')).first()

        shift = Shift(eventtype, time, datetime.now().date(), 'Confirmed', role, None, location.locationid)

        vol = Volunteer(None, firstname, lastname, phone, None)
        db.session.add(vol)
        db.session.commit()
        vol = Volunteer.query.filter_by(first_name=firstname, last_name=lastname, van_id=None).first()

        shift.person = vol.id

        db.session.add(vol)
        db.session.add(shift)
        db.session.commit()

        return redirect('/consolidated/' + office + '/' + page)

    except:
        abort(500)
        return redirect('/consolidated')


@oid.require_login
@app.route('/dashboard')
def dashboard():
    user = User.query.filter_by(email=g.users.email).first()
    dashboard_permission = user.rank == 'DATA' or user.rank == 'Field Director'

    if not dashboard_permission:
        return redirect('/consolidated')
    
    return redirect('/consolidated')

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/consolidated')

@app.errorhandler(500)
def internal_service_error(e):
    return redirect('/consolidated')

if __name__ == "__main__":
    app.run()
