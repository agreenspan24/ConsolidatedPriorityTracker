from datetime import datetime

from flask import flash, g, redirect, render_template, request, session

from sqlalchemy import and_

from app import app, oid
from config import settings
from cptvanapi import CPTVANAPI
from models import *
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
            return redirect('/')
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
            return redirect('/')    
        
        

@app.route('/logout', methods=['GET'])
def logout():
    g.user = None
    session.pop('openid', None)
    return redirect('/login')

@oid.require_login
@app.route('/', methods=['POST','GET'])
def index():
    email = g.user.email
    print(email)
    offices = Location.query.all()
    if request.method == 'POST':
        office = request.form.get('office')
        date = datetime.today().strftime('%Y-%m-%d')
        shifts = Shift.query.filter_by(shift_location=office, date=date).all()


        return render_template('flake.html', offices=offices, shifts=shifts)


    return render_template('filter.html', offices=offices, email=email, shifts=None)

@oid.require_login
@app.route('/shifts', methods=['GET','POST'])
def test():
    office = request.args.get('office')
    date = datetime.today().strftime('%Y-%m-%d')

    if office:
            
        shifts = Shift.query.filter(and_(Shift.locationname.like(office +'%'),Shift.startdate==date)).all()   
        return render_template('filter.html', shifts=shifts)

@oid.require_login
@app.route('/kph', methods=['GET', 'POST'])
def kph():
    office = request.args.get('office')

    


if __name__ == "__main__":
    app.run()
