from flask import request, g, Response, jsonify
from services import SocketIoService
from datetime import datetime, timedelta
from dateutil.parser import parse
from models import db, Volunteer, Shift, CanvassGroup, SyncShift
from sqlalchemy.orm import joinedload
from utility import str_sanitize
import urllib
import time
import re

# PassService updates values in the database as they're edited by users. 
# It does a good bit of data sanitization as it comes in. 
class PassService:
    def add_pass(self, office, page):
        keys = list(request.form.keys())
        parent_id = request.form.get('parent_id')
        page_load_time = datetime.strptime(urllib.parse.unquote(request.form.get('page_load_time')), '%I:%M %p').time()

        if not parent_id or not parent_id.isdigit():
            return Response('Invalid ID', 400)

        return_var = None
        
        office = str_sanitize(office)
        page = str_sanitize(page)
        action_type = 'OTHER'
        
        if page == 'kph':
            if 'claim' in keys:
                group = CanvassGroup.query.get(parent_id)
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
                    
                    action_type = 'UNCLAIM'
                    group.claim = None
                    return_var = jsonify({
                        'name': 'Claim',
                        'color': None
                    })
                else:
                    action_type = 'CLAIM'
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

                    if isinstance(shifts, str):
                        return Response(shifts, 400)

                    for shift in shifts:
                        if return_var == None:
                            return_var = []

                        return_var.append({
                            'id': shift.id,
                            'vol_id': shift.volunteer.id, 
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

                elif 'check_in_time' in keys:
                    check_in_time = request.form.get('check_in_time')

                    try:
                        group.check_in_time = parse(check_in_time) if not check_in_time in [None, ''] else None
                    except:
                        return Response('Invalid Time', 400)

                    note = group.add_note('kph', 'Next Check In changed to ' + (group.check_in_time.strftime('%I:%M %p') if group.check_in_time else 'None'), g.user)
                    
                    return_var = note

                elif 'note' in keys:
                    note_text = request.form.get('note')

                    note_text = str_sanitize(note_text)

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
                    packet_names = str_sanitize(packet_names)

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
                    action_type = 'UNCLAIM'
                    return_var = jsonify({
                        'name': 'Claim',
                        'color': None
                    })
                else:
                    shift.claim = g.user.id
                    action_type = 'CLAIM'
                    return_var = jsonify({
                        'name': g.user.claim_name(),
                        'color': g.user.color
                    })

            else:
                if 'status' in keys:
                    status = request.form.get('status')
                    status = str_sanitize(status)

                    if not status in ['Completed', 'Declined', 'No Show', 'Resched', 'Same Day Confirmed', 'In', 'Scheduled', 'Invited', 'Left Message']:
                        return Response('Invalid status', status=400)

                    return_var = shift.flip(page, status, g.user)    

                elif 'first_name' in keys:
                    first = request.form.get('first_name')

                    if shift.volunteer.updated_by_other(page_load_time, g.user):
                        return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

                    first = str_sanitize(first)

                    vol = Volunteer.query.filter_by(first_name=first, last_name=shift.volunteer.last_name, phone_number=shift.volunteer.phone_number).order_by(Volunteer.van_id).first()

                    if vol:
                        shift.volunteer = vol
                        shift.person = vol.id

                    else:
                        shift.volunteer.first_name = first 

                elif 'last_name' in keys:
                    last = request.form.get('last_name')

                    if shift.volunteer.updated_by_other(page_load_time, g.user):
                        return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

                    last = str_sanitize(last)
                    
                    vol = Volunteer.query.filter_by(first_name=shift.volunteer.first_name, last_name=last, phone_number=shift.volunteer.phone_number).order_by(Volunteer.van_id).first()

                    if vol:
                        shift.volunteer = vol
                        shift.person = vol.id

                    else:
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
                    else:
                        shift.volunteer.van_id = None
                
                elif 'phone' in keys:
                    phone = request.form.get('phone')

                    if shift.volunteer.updated_by_other(page_load_time, g.user):
                        return Response('This volunteer has been updated by ' + g.user.email + ' since you last loaded the page. Please refresh and try again.', 400)

                    phone_sanitized = re.sub('[- ().+]', '', phone)

                    if phone_sanitized and not phone_sanitized.isdigit():
                        return Response('Invalid Phone', status=400)
                    
                    vol = Volunteer.query.filter_by(first_name=shift.volunteer.first_name, last_name=shift.volunteer.last_name, phone_number=phone_sanitized).order_by(Volunteer.van_id).first()

                    if vol:
                        shift.volunteer = vol
                        shift.person = vol.id

                    else:
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

                    note_text = str_sanitize(note_text)

                    return_var = shift.add_note(page, note_text, g.user)

                elif 'passes' in keys:
                    return_var = str(shift.add_pass(page))
                
                shift.last_update = datetime.now().time()
                shift.last_user = g.user.id
        
        # Broadcast to anyone in this room (that is, the relevant office) that the page has
        # updates. User ID is passed so we don't highlight/disable for the user herself; user
        # name is passed so it can be easily added to the page
        # Note that time.time() is the UNIX timestamp
        json = { 'item_id': parent_id, 'page': page, 'user_id': g.user.id, \
                'user_color': g.user.color, 'user_short_name': g.user.claim_name(), \
                'action_type': action_type, 'keys': keys, 'viewed_at': int(time.time()) }

        socketIoService = SocketIoService.SocketIoService()
        socketIoService.emit_update('updates', office, page, json, propogate=True)

        print('JSON blog {}'.format(json))

        db.session.commit()

        return return_var if return_var else ''