from app import socketio
from models import Location
import re

class SocketIoService:
    # Office name should begin with region name, i.e. office R1B is part of Region 1.
    # Otherwise, it's not in any region, so no need to propagate to region pages
    def office_to_region(self, office):
        if re.match(r'.+[A-Z]$', office):
            return office[0:-1]
        else:
            return office

    def room_name(self, office, page):
        return '{}-{}'.format(office, page)

    def is_region(self, office):
        return re.match(r'.+[0-9]$', office)

    def emit_update(self, topic, office, page, json, propogate=False):
        room = self.room_name(office, page)
        socketio.emit(topic, json, room = room, namespace = '/live-updates')
        
        print("{}/{}: {}".format(topic, room, json))
        
        if propogate:
            # Also emit a message to the room representing this region
            if not self.is_region(office):
                room = self.room_name(self.office_to_region(office), page)
                print("{}/{} (region): {}".format(topic, room, json))
                socketio.emit(topic, json, room = room, namespace='/live-updates')
                
            # if this IS a region, emit to all the child offices
            else:
                locations = Location.query.filter_by(region=office).all()
                for location in locations:
                    matches = re.match(r'^(R[0-9][A-Z]).+', location.locationname)
                    if matches:
                        room = self.room_name(self.office_to_region(matches.group(1)), page)
                        print("{}/{} (office): {}".format(topic, room, json))
                        socketio.emit(topic, json, room = room, namespace='/live-updates')
