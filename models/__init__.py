from app import app, db
from models import syncshift, location, shiftstatus, \
    eventtype, volunteer, note, user, canvassgroup, \
    shift, shiftstats, headerstats, backupgroup, backupshift

SyncShift = syncshift.SyncShift
Location = location.Location
ShiftStatus = shiftstatus.ShiftStatus
EventType = eventtype.EventType
Volunteer = volunteer.Volunteer
Note = note.Note
User = user.User
CanvassGroup = canvassgroup.CanvassGroup
Shift = shift.Shift
ShiftStats = shiftstats.ShiftStats
HeaderStats = headerstats.HeaderStats
BackupGroup = backupgroup.BackupGroup
BackupShift = backupshift.BackupShift
