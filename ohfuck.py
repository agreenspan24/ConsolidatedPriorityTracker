import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email import encoders
from datetime import datetime
import csv
from app import app
from models import db, Volunteer, Location, Shift, Note, User, ShiftStats, CanvassGroup, HeaderStats, SyncShift, BackupGroup, BackupShift
from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import joinedload

def auth_gmail():
    # Credentials (if needed)
    mailusername = os.environ['mailemail']
    mailpassword = os.environ['mailpass']
    # The actual mail send
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.ehlo()
    server.login(mailusername,mailpassword)
    return server

server = auth_gmail()

date = datetime.today().strftime('%Y-%m-%d')

if date >= '2018-10-19' and date <= '2018-10-21':
    sldcsv = csv.reader(open('failsafe/dr1.csv'))

elif date >= '2018-10-22' and date <= '2018-10-25':
    sldcsv = csv.reader(open('failsafe/p1mw.csv'))

elif date >= '2018-10-26' and date <= '2018-10-28':
    sldcsv = csv.reader(open('failsafe/dr2.csv'))

elif date >= '2018-10-29' and date <= '2018-11-01':
    sldcsv = csv.reader(open('failsafe/dr2.csv'))

elif date >= '2018-11-02' and date <= '2018-11-06':
    sldcsv = csv.reader(open('failsafe/final5.csv'))
else:
    print("You don't need this anymore")


for row in sldcsv:
    if row[2] is not '':
        office = row[0]
        locations = Location.query.filter(Location.locationname.like(office + '%')).all()
        location_ids = list(map(lambda l: l.locationid, locations))
        shifts = Shift.query.filter(Shift.is_active == True, Shift.shift_location.in_(location_ids)).order_by(asc(Shift.time), asc(Shift.person)).all()


        with open('failsafe/backups/{date}{office}sdc.csv'.format(date=date, office=office), 'w') as sdc:
            writer = csv.writer(sdc)
            writer.writerow([office, date, 'Same Day Confirms'])
            writer.writerow(['VanId', 'Name', 'Phone', 'Cell Phone', 'Time', 'Location', 'Event Type', 'Role', 'Status'])
            for s in shifts:
                writer.writerow([s.volunteer.van_id,
                s.volunteer.first_name + " " + s.volunteer.last_name, 
                s.volunteer.phone_number,
                s.volunteer.cellphone,
                s.time,
                s.location.locationname,
                s.eventtype,
                s.role,
                s.status])

        all_groups = CanvassGroup.query.options(joinedload(CanvassGroup.canvass_shifts)).filter_by(is_active=True).all()
        groups = []

        for gr in all_groups:
            if gr.canvass_shifts[0].shift_location in location_ids and gr.canvass_shifts[0].id in list(map(lambda s: s.id, shifts)):
                groups.append(gr)

        
            
        
        with open('failsafe/backups/{date}{office}kph.csv'.format(date=date, office=office), 'w') as kph:
            writer = csv.writer(kph)
            writer.writerow([office, date, 'KPH'])
            writer.writerow(['VanId', 'Name', 'Phone', 'Cell Phone', 'Packets Given', 'Packet Names', 'Actual', 'Goal', 'Returned?'])
            for gr in groups:
                vanids = []
                names = []
                phone_numbers = []
                cell_numbers = []
                for s in gr.canvass_shifts:
                    vanids.append(s.volunteer.van_id)
                    names.append(s.volunteer.first_name + " " + s.volunteer.last_name)
                    phone_numbers.append(s.volunteer.phone_number)
                    cell_numbers.append(s.volunteer.cellphone)

                writer.writerow([vanids, names, phone_numbers, cell_numbers,
                    gr.packets_given,
                    gr.packet_names,
                    gr.last_check_in,
                    gr.actual,
                    gr.goal,
                    gr.is_returned])
        
        with open('failsafe/backups/{date}{office}flake.csv'.format(date=date, office=office), 'w') as flake:
            writer = csv.writer(flake)
            writer.writerow([office, date, 'Flake Chase'])
            writer.writerow(['VanId', 'Name', 'Phone', 'Cell Phone', 'Time', 'Location', 'Event Type', 'Role', 'Status'])
            for s in shifts:
                if flake:
                    writer.writerow([s.volunteer.van_id,
                    s.volunteer.first_name + " " + s.volunteer.last_name, 
                    s.volunteer.phone_number,
                    s.volunteer.cellphone,
                    s.time,
                    s.location.locationname,
                    s.eventtype,
                    s.role,
                    s.status])


        msg = MIMEMultipart()
        msg['From'] = mailusername
        msg['To'] = row[3]
        msg['Subject'] = 'Consolidated Backup'

        sdcattach = MIMEBase('application', "octet-stream")
        kphattach = MIMEBase('application', "octet-stream")
        flakeattach = MIMEBase('application', "octet-stream")
        
        sdcattach.set_payload(open("failsafe/backups/{date}{office}sdc.csv".format(date=date, office=office), "rb").read())
        kphattach.set_payload(open("failsafe/backups/{date}{office}kph.csv".format(date=date, office=office), "rb").read())
        flakeattach.set_payload(open("failsafe/backups/{date}{office}flake.csv".format(date=date, office=office), "rb").read())
        
        encoders.encode_base64(sdcattach)
        encoders.encode_base64(kphattach)
        encoders.encode_base64(flakeattach)

        sdcattach.add_header('Content-Disposition', 'attachment', filename="{date}{office}sdc.csv".format(date=date, office=office))
        kphattach.add_header('Content-Disposition', 'attachment', filename="{date}{office}kph.csv".format(date=date, office=office))
        flakeattach.add_header('Content-Disposition', 'attachment', filename="{date}{office}flake.csv".format(date=date, office=office))
        
        msg.attach(sdcattach)
        msg.attach(kphattach)
        msg.attach(flakeattach)
        server.sendmail('wbliss@missouridems.org', row[3],msg.as_string())

        print(office, row[3] + ' sent')