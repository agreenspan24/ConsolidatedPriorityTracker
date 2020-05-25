

class ShiftStats:
    def __init__(self, shifts, groups):
        self.vol_confirmed = 0
        self.vol_completed = 0
        self.vol_declined = 0
        self.vol_unflipped = 0
        self.vol_flaked = 0
        self.intern_completed = 0
        self.intern_declined = 0
        self.kps = 0
        self.actual = 0
        self.goal = 0
        self.percent_to_goal = 0.00
        self.packets_out = 0
        self.canvassers_out = 0
        self.shifts_not_pitched = 0
        self.extra_shifts_sched = 0

        for s in shifts:
            if s.eventtype == "Intern DVC":
                if s.status in ["Completed", "In"]:
                    self.intern_completed += 1
                if s.status == "Declined":
                    self.intern_declined += 1
            elif s.eventtype == "Volunteer DVC" and s.role == "Canvassing":
                if s.status == "Same Day Confirmed":
                    self.vol_confirmed += 1
                if s.status in ["Completed", "In"]:
                    self.vol_completed += 1
                if s.status == "Declined":
                    self.vol_declined += 1
                if s.status in ["Scheduled", 'Confirmed', 'Same Day Confirmed', 'Sched-Web']:
                    self.vol_unflipped += 1
                if s.status == "No Show":
                    self.vol_flaked += 1
            if s.status == 'In' and s.role == 'Canvassing':
                self.canvassers_out += 1

            if s.status == 'Completed' and s.canvass_group != None:
                if s.volunteer.has_pitched_today in [None, False]:
                    self.shifts_not_pitched += 1
                elif s.volunteer.extra_shifts_sched:
                    self.extra_shifts_sched += s.volunteer.extra_shifts_sched


        knocks = 0
        for g in groups:
            if g.is_returned:
                knocks += g.actual
            else:
                self.packets_out += g.packets_given
            self.actual += g.actual
            self.goal += g.goal

        shifts = self.intern_completed + self.vol_completed
        self.kps = knocks / (shifts if shifts > 0 else 1)

        self.percent_to_goal = self.actual / (self.goal if self.goal > 0 else 1)

