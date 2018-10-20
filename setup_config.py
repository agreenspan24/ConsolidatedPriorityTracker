black_list = []

rural_locations = {
   'R4: Secondary Turf' : 'R4F - Rural',
   'R4: Bootheel' : 'R4F - Rural', 
   'R4F - West Plains McDonalds' : 'R4F - Rural',
   'R4F - Secondary Turf Sikeston' : 'R4F - Rural',
   'R4F - Perryville Staging Location' : 'R4F - Rural',
   'R4: Secondary Turf Farmington' : 'R4F - Rural',
   'R4F - Secondary Turf': 'R4F - Rural'
}

dashboard_query = """
CREATE VIEW consolidated.dashboard_totals AS 
WITH confirm_attempt_totals AS (
	
	SELECT shift_location
	, SUM(CASE WHEN role = 'Canvassing' THEN 1 ELSE 0 END) canvass_total_scheduled
	, SUM(CASE WHEN role = 'Canvassing' AND s.status = 'Same Day Confirmed' THEN 1 ELSE 0 END) canvass_same_day_confirmed
	, SUM(CASE WHEN role = 'Canvassing' AND s.status = 'Completed' THEN 1 ELSE 0 END) canvass_completed
	, SUM(CASE WHEN role = 'Canvassing' AND s.status = 'Declined' THEN 1 ELSE 0 END) canvass_declined
	, SUM(CASE WHEN role = 'Canvassing' AND s.flake THEN 1 ELSE 0 END) canvass_flaked
	, SUM(CASE WHEN role = 'Phonebanking' THEN 1 ELSE 0 END) phone_total_scheduled
	, SUM(CASE WHEN role = 'Phonebanking' AND s.status = 'Same Day Confirmed' THEN 1 ELSE 0 END) phone_same_day_confirmed
	, SUM(CASE WHEN role = 'Phonebanking' AND s.status = 'Completed' THEN 1 ELSE 0 END) phone_completed
	, SUM(CASE WHEN role = 'Phonebanking' AND s.status = 'Declined' THEN 1 ELSE 0 END) phone_declined
	, SUM(CASE WHEN role = 'Phonebanking' AND s.flake THEN 1 ELSE 0 END) phone_flaked
	, SUM(CASE WHEN s.flake THEN 1 ELSE 0 END) flake_total
	, SUM(CASE WHEN s.flake AND NOT s.status = 'No Show' THEN 1 ELSE 0 END) flake_attempts
	, SUM(CASE WHEN s.flake AND s.status = 'Rescheduled' THEN 1 ELSE 0 END) flake_rescheduled
	FROM consolidated.shift s
	WHERE s.is_active = true
	GROUP BY 1
	
), canvass_group_totals AS (
	
	SELECT s.shift_location, cg.id, cg.actual, cg.goal, cg.packets_given, cg.check_in_time, cg.is_returned, cg.departure
	, COUNT(*)::bigint group_canvassers
	FROM consolidated.canvass_group cg
	JOIN consolidated.shift s
	ON cg.id = s.canvass_group
	WHERE cg.is_active = true
	AND s.is_active = true
	GROUP BY 1, 2
	
), canvass_totals AS (
	
	SELECT shift_location
	, SUM(group_canvassers) canvassers_all_day
	, SUM(actual) actual_all_day
	, SUM(goal) goal_all_day
	, SUM(packets_given) packets_all_day
	, SUM(CASE WHEN NOT is_returned THEN group_canvassers ELSE 0 END) canvassers_out_now
	, SUM(CASE WHEN NOT is_returned THEN actual ELSE 0 END) actual_out_now
	, SUM(CASE WHEN NOT is_returned THEN goal ELSE 0 END) goal_out_now
	, SUM(CASE WHEN NOT is_returned THEN packets_given ELSE 0 END) packets_out_now
	, SUM(CASE WHEN NOT is_returned AND departure IS NOT NULL AND check_in_time IS NOT NULL AND check_in_time < (current_time - interval '5 hours') THEN 1 ELSE 0 END) overdue_check_in
	FROM canvass_group_totals
	GROUP BY 1
	
), office_totals AS (SELECT l.region, l.locationname AS office
, COALESCE(cat.canvass_total_scheduled, 0) canvass_total_scheduled
, COALESCE(cat.canvass_same_day_confirmed, 0) canvass_same_day_confirmed
, COALESCE(cat.canvass_same_day_confirmed * 1.0 / (CASE WHEN cat.canvass_total_scheduled < 1 THEN 1 ELSE cat.canvass_total_scheduled END), 0) canvass_same_day_confirmed_perc
, COALESCE(cat.canvass_completed, 0) canvass_completed
, COALESCE(cat.canvass_completed * 1.0 / (CASE WHEN cat.canvass_total_scheduled < 1 THEN 1 ELSE cat.canvass_total_scheduled END), 0) canvass_completed_perc
, COALESCE(cat.canvass_declined, 0) canvass_declined
, COALESCE(cat.canvass_declined * 1.0 / (CASE WHEN cat.canvass_total_scheduled < 1 THEN 1 ELSE cat.canvass_total_scheduled END), 0) canvass_declined_perc
, COALESCE(cat.canvass_flaked, 0) canvass_flaked
, COALESCE(cat.canvass_flaked * 1.0 / (CASE WHEN cat.canvass_total_scheduled < 1 THEN 1 ELSE cat.canvass_total_scheduled END), 0) canvass_flaked_perc
, COALESCE(cat.phone_total_scheduled, 0) phone_total_scheduled
, COALESCE(cat.phone_same_day_confirmed, 0) phone_same_day_confirmed
, COALESCE(cat.phone_same_day_confirmed * 1.0 / (CASE WHEN cat.phone_total_scheduled < 1 THEN 1 ELSE cat.phone_total_scheduled END), 0) phone_same_day_confirmed_perc
, COALESCE(cat.phone_completed, 0) phone_completed
, COALESCE(cat.phone_completed * 1.0 / (CASE WHEN cat.phone_total_scheduled < 1 THEN 1 ELSE cat.phone_total_scheduled END), 0) phone_completed_perc
, COALESCE(cat.phone_declined, 0) phone_declined
, COALESCE(cat.phone_declined * 1.0 / (CASE WHEN cat.phone_total_scheduled < 1 THEN 1 ELSE cat.phone_total_scheduled END), 0) phone_declined_perc
, COALESCE(cat.phone_flaked, 0) phone_flaked
, COALESCE(cat.phone_flaked * 1.0 / (CASE WHEN cat.phone_total_scheduled < 1 THEN 1 ELSE cat.phone_total_scheduled END), 0) phone_flaked_perc
, COALESCE(cat.flake_total, 0) flake_total
, COALESCE(cat.flake_attempts, 0) flake_attempts
, COALESCE(cat.flake_attempts * 1.0 / (CASE WHEN cat.flake_total < 1 THEN 1 ELSE cat.flake_total END), 0) flake_attempts_perc
, COALESCE(cat.flake_rescheduled, 0) flake_rescheduled
, COALESCE(cat.flake_rescheduled * 1.0 / (CASE WHEN cat.flake_total < 1 THEN 1 ELSE cat.flake_total END), 0) flake_rescheduled_perc
, COALESCE(cat.flake_total - cat.flake_attempts, 0) flake_chase_remaining
, COALESCE((cat.flake_total - cat.flake_attempts) * 1.0 / (CASE WHEN cat.flake_total < 1 THEN 1 ELSE cat.flake_total END), 0) flake_chase_remaining_perc
, COALESCE(ct.canvassers_all_day, 0) canvassers_all_day
, COALESCE(ct.actual_all_day, 0) actual_all_day
, COALESCE(ct.goal_all_day, 0) goal_all_day
, COALESCE(ct.packets_all_day, 0) packets_out_all_day
, COALESCE(ct.actual_all_day * 1.0 / (CASE WHEN ct.canvassers_all_day < 1 THEN 1 ELSE ct.canvassers_all_day END), 0) kps
, COALESCE(ct.canvassers_out_now, 0) canvassers_out_now
, COALESCE(ct.actual_out_now, 0) actual_out_now
, COALESCE(ct.goal_out_now, 0) goal_out_now
, COALESCE(ct.packets_out_now, 0) packets_out_now
, COALESCE(ct.actual_out_now * 1.0 / (CASE WHEN ct.canvassers_out_now < 1 THEN 1 ELSE ct.canvassers_out_now END), 0) kph
, COALESCE(ct.overdue_check_in, 0) overdue_check_ins
FROM consolidated.location l 
LEFT JOIN confirm_attempt_totals cat
	ON l.locationid = cat.shift_location
LEFT JOIN canvass_totals ct
	ON l.locationid = ct.shift_location
WHERE NOT region IN ('In', 'Ou', 'Th')
), region_totals AS (SELECT region, region || ' Total' office
, SUM(canvass_total_scheduled)::bigint canvass_total_scheduled
, SUM(canvass_same_day_confirmed)::bigint canvass_same_day_confirmed
, AVG(canvass_same_day_confirmed_perc) canvass_same_day_confirmed_perc
, SUM(canvass_completed)::bigint canvass_completed
, AVG(canvass_completed_perc) canvass_completed_perc
, SUM(canvass_declined)::bigint canvass_declined
, AVG(canvass_declined_perc) canvass_declined_perc
, SUM(canvass_flaked)::bigint canvass_flaked
, AVG(canvass_flaked_perc) canvass_flaked_perc
, SUM(phone_total_scheduled)::bigint phone_total_scheduled
, SUM(phone_same_day_confirmed)::bigint phone_same_day_confirmed
, AVG(phone_same_day_confirmed_perc) phone_same_day_confirmed_perc
, SUM(phone_completed)::bigint phone_completed
, AVG(phone_completed_perc) phone_completed_perc
, SUM(phone_declined)::bigint phone_declined
, AVG(phone_declined_perc) phone_declined_perc
, SUM(phone_flaked)::bigint phone_flaked
, AVG(phone_flaked_perc) phone_flaked_perc
, SUM(flake_total)::bigint flake_total
, SUM(flake_attempts)::bigint flake_attempts
, AVG(flake_attempts_perc) flake_attempts_perc
, SUM(flake_rescheduled)::bigint flake_rescheduled
, AVG(flake_rescheduled_perc) flake_rescheduled_perc
, SUM(flake_chase_remaining)::bigint flake_chase_remaining
, AVG(flake_chase_remaining_perc) flake_chase_remaining_perc
, SUM(canvassers_all_day)::bigint canvassers_all_day
, SUM(actual_all_day)::bigint actual_all_day
, SUM(goal_all_day)::bigint goal_all_day
, SUM(packets_out_all_day)::bigint packets_out_all_day
, AVG(kps) kps
, SUM(canvassers_out_now)::bigint canvassers_out_now
, SUM(actual_out_now)::bigint actual_out_now
, SUM(goal_out_now)::bigint goal_out_now
, SUM(packets_out_now)::bigint packets_out_now
, AVG(kph) kph
, SUM(overdue_check_ins)::bigint overdue_check_ins
FROM office_totals
GROUP BY region
HAVING not region = 'Ou'
), state_totals AS (
	SELECT 'Missouri' region, 'State Total' office
, SUM(canvass_total_scheduled)::bigint canvass_total_scheduled
, SUM(canvass_same_day_confirmed)::bigint canvass_same_day_confirmed
, AVG(canvass_same_day_confirmed_perc) canvass_same_day_confirmed_perc
, SUM(canvass_completed)::bigint canvass_completed
, AVG(canvass_completed_perc) canvass_completed_perc
, SUM(canvass_declined)::bigint canvass_declined
, AVG(canvass_declined_perc) canvass_declined_perc
, SUM(canvass_flaked)::bigint canvass_flaked
, AVG(canvass_flaked_perc) canvass_flaked_perc
, SUM(phone_total_scheduled)::bigint phone_total_scheduled
, SUM(phone_same_day_confirmed)::bigint phone_same_day_confirmed
, AVG(phone_same_day_confirmed_perc) phone_same_day_confirmed_perc
, SUM(phone_completed)::bigint phone_completed
, AVG(phone_completed_perc) phone_completed_perc
, SUM(phone_declined)::bigint phone_declined
, AVG(phone_declined_perc) phone_declined_perc
, SUM(phone_flaked)::bigint phone_flaked
, AVG(phone_flaked_perc) phone_flaked_perc
, SUM(flake_total)::bigint flake_total
, SUM(flake_attempts)::bigint flake_attempts
, AVG(flake_attempts_perc) flake_attempts_perc
, SUM(flake_rescheduled)::bigint flake_rescheduled
, AVG(flake_rescheduled_perc) flake_rescheduled_perc
, SUM(flake_chase_remaining)::bigint flake_chase_remaining
, AVG(flake_chase_remaining_perc) flake_chase_remaining_perc
, SUM(canvassers_all_day)::bigint canvassers_all_day
, SUM(actual_all_day)::bigint actual_all_day
, SUM(goal_all_day)::bigint goal_all_day
, SUM(packets_out_all_day)::bigint packets_out_all_day
, AVG(kps) kps
, SUM(canvassers_out_now)::bigint canvassers_out_now
, SUM(actual_out_now)::bigint actual_out_now
, SUM(goal_out_now)::bigint goal_out_now
, SUM(packets_out_now)::bigint packets_out_now
, AVG(kph) kph
, SUM(overdue_check_ins)::bigint overdue_check_ins
FROM office_totals
)

(SELECT * 
	FROM office_totals)
UNION 
(SELECT * 
	FROM region_totals)
UNION 
(SELECT * 
	FROM state_totals)

ORDER BY region, office


"""




