from datetime import datetime

from flask import flash, g, redirect, render_template, request, session

from sqlalchemy import and_, asc

from app import app, oid
from config import settings
##from cptvanapi import CPTVANAPI
from models import db, Volunteer, Location, Shift, Note, User
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

        print('option')
        if option == "Dashboard":
            redirect('/dashboard')

        office = request.form.get('office')
        page = request.form.get('page')
        print(office, page)
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
    for location in locations:
        shifts = Shift.query.filter_by(shift_location=location.locationid, date=date).all()
        for shift in shifts:
            all_shifts.append(shift)

    if page == 'sdc':
        return render_template('same_day_confirms.html', active_tab="sdc", location=location, shifts=shifts)

    elif page == 'kph':
        return render_template('kph.html', active_tab="kph", location=location, shifts=shifts)

    elif page == 'flake':
        return render_template('flake.html', active_tab="flake", location=location, shifts=shifts)

    elif page == 'stats':
        stats = ShiftStats(shifts)
        print(stats.vol_confirmed)
        print(location)
        return render_template('office_totals.html', active_tab="stats", location=location, stats=stats)

    else:
        return redirect('/consolidated' + str(location.locationname)[0:3] + '/sdc')

@oid.require_login
@app.route('/consolidated/<office>/<page>/pass', methods=['POST'])
def add_pass(office, page):
    shift_id = request.form.get('shift_id')
    shift = Shift.query.get(shift_id).all()

    if page == 'flake':
        shift.flake_pass += 1
        shift.notes += request.form.get('note')

        db.session.add(shift)
        db.session.commit()
    
    return redirect('/consolidated/' + office + '/' + page)

@oid.require_login
@app.route('/dashboard')
def dashboard():
    user = User.query.filter_by(email=g.user.email).first()
    dashboard_permission = user.rank == 'DATA' or user.rank == 'Field Director'

    if not dashboard_permission:
        redirect('/consolidated')
    
    redirect('/consolidated')

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/consolidated')

@app.errorhandler(500)
def internal_service_error(e):
    return redirect('/consolidated')

if __name__ == "__main__":
    app.run()
