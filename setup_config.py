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
<<<<<<< HEAD
 WITH confirm_attempt_totals AS (
         SELECT s.shift_location,
            sum(
                CASE
                    WHEN s.role::text = 'Canvassing'::text THEN 1
                    ELSE 0
                END) AS canvass_total_scheduled,
            sum(
                CASE
                    WHEN s.role::text = 'Canvassing'::text AND s.status::text = 'Same Day Confirmed'::text THEN 1
                    ELSE 0
                END) AS canvass_same_day_confirmed,
            sum(
                CASE
                    WHEN s.role::text = 'Canvassing'::text AND s.status::text = 'Completed'::text OR s.status::text = 'In'::text THEN 1
                    ELSE 0
                END) AS canvass_completed,
            sum(
                CASE
                    WHEN s.role::text = 'Canvassing'::text AND s.status::text = 'Declined'::text THEN 1
                    ELSE 0
                END) AS canvass_declined,
            sum(
                CASE
                    WHEN s.role::text = 'Canvassing'::text AND s.flake THEN 1
                    ELSE 0
                END) AS canvass_flaked,
            sum(
                CASE
                    WHEN s.role::text = 'Phonebanking'::text THEN 1
                    ELSE 0
                END) AS phone_total_scheduled,
            sum(
                CASE
                    WHEN s.role::text = 'Phonebanking'::text AND s.status::text = 'Same Day Confirmed'::text THEN 1
                    ELSE 0
                END) AS phone_same_day_confirmed,
            sum(
                CASE
                    WHEN s.role::text = 'Phonebanking'::text AND s.status::text = 'Completed'::text THEN 1
                    ELSE 0
                END) AS phone_completed,
            sum(
                CASE
                    WHEN s.role::text = 'Phonebanking'::text AND s.status::text = 'Declined'::text THEN 1
                    ELSE 0
                END) AS phone_declined,
            sum(
                CASE
                    WHEN s.role::text = 'Phonebanking'::text AND s.flake THEN 1
                    ELSE 0
                END) AS phone_flaked,
            sum(
                CASE
                    WHEN s.flake THEN 1
                    ELSE 0
                END) AS flake_total,
            sum(
                CASE
                    WHEN s.flake AND NOT s.status::text = 'No Show'::text THEN 1
                    ELSE 0
                END) AS flake_attempts,
            sum(
                CASE
                    WHEN s.flake AND s.status::text = 'Rescheduled'::text THEN 1
                    ELSE 0
                END) AS flake_rescheduled
           FROM {0}.shift s
          WHERE s.is_active = true
          GROUP BY s.shift_location
        ), canvass_group_totals AS (
         SELECT s.shift_location,
            cg.id,
            cg.actual,
            cg.goal,
            cg.packets_given,
            cg.check_in_time,
            cg.is_returned,
            cg.departure,
            count(*) AS group_canvassers
           FROM {0}.canvass_group cg
             JOIN {0}.shift s ON cg.id = s.canvass_group
          WHERE cg.is_active = true
          GROUP BY s.shift_location, cg.id
        ), canvass_totals AS (
         SELECT canvass_group_totals.shift_location,
            sum(canvass_group_totals.group_canvassers) AS canvassers_all_day,
            sum(canvass_group_totals.actual) AS actual_all_day,
            sum(canvass_group_totals.goal) AS goal_all_day,
            sum(canvass_group_totals.packets_given) AS packets_all_day,
            sum(
                CASE
                    WHEN NOT canvass_group_totals.is_returned THEN canvass_group_totals.group_canvassers
                    ELSE 0::bigint
                END) AS canvassers_out_now,
            sum(
                CASE
                    WHEN NOT canvass_group_totals.is_returned THEN canvass_group_totals.actual
                    ELSE 0
                END) AS actual_out_now,
            sum(
                CASE
                    WHEN NOT canvass_group_totals.is_returned THEN canvass_group_totals.goal
                    ELSE 0
                END) AS goal_out_now,
            sum(
                CASE
                    WHEN NOT canvass_group_totals.is_returned THEN canvass_group_totals.packets_given
                    ELSE 0
                END) AS packets_out_now,
            sum(
                CASE
                    WHEN NOT canvass_group_totals.is_returned AND canvass_group_totals.departure IS NOT NULL AND canvass_group_totals.check_in_time IS NOT NULL AND canvass_group_totals.check_in_time::time with time zone < (CURRENT_TIME - '05:00:00'::interval) THEN 1
                    ELSE 0
                END) AS overdue_check_in
           FROM canvass_group_totals
          GROUP BY canvass_group_totals.shift_location
        ), office_totals AS (
         SELECT l.region,
            l.locationname AS office,
            COALESCE(cat.canvass_total_scheduled, 0::bigint) AS canvass_total_scheduled,
            COALESCE(cat.canvass_same_day_confirmed, 0::bigint) AS canvass_same_day_confirmed,
            COALESCE(cat.canvass_same_day_confirmed::numeric * 1.0 /
                CASE
                    WHEN cat.canvass_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.canvass_total_scheduled
                END::numeric, 0::numeric) AS canvass_same_day_confirmed_perc,
            COALESCE(cat.canvass_completed, 0::bigint) AS canvass_completed,
            COALESCE(cat.canvass_completed::numeric * 1.0 /
                CASE
                    WHEN cat.canvass_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.canvass_total_scheduled
                END::numeric, 0::numeric) AS canvass_completed_perc,
            COALESCE(cat.canvass_declined, 0::bigint) AS canvass_declined,
            COALESCE(cat.canvass_declined::numeric * 1.0 /
                CASE
                    WHEN cat.canvass_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.canvass_total_scheduled
                END::numeric, 0::numeric) AS canvass_declined_perc,
            COALESCE(cat.canvass_flaked, 0::bigint) AS canvass_flaked,
            COALESCE(cat.canvass_flaked::numeric * 1.0 /
                CASE
                    WHEN cat.canvass_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.canvass_total_scheduled
                END::numeric, 0::numeric) AS canvass_flaked_perc,
            COALESCE(cat.phone_total_scheduled, 0::bigint) AS phone_total_scheduled,
            COALESCE(cat.phone_same_day_confirmed, 0::bigint) AS phone_same_day_confirmed,
            COALESCE(cat.phone_same_day_confirmed::numeric * 1.0 /
                CASE
                    WHEN cat.phone_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.phone_total_scheduled
                END::numeric, 0::numeric) AS phone_same_day_confirmed_perc,
            COALESCE(cat.phone_completed, 0::bigint) AS phone_completed,
            COALESCE(cat.phone_completed::numeric * 1.0 /
                CASE
                    WHEN cat.phone_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.phone_total_scheduled
                END::numeric, 0::numeric) AS phone_completed_perc,
            COALESCE(cat.phone_declined, 0::bigint) AS phone_declined,
            COALESCE(cat.phone_declined::numeric * 1.0 /
                CASE
                    WHEN cat.phone_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.phone_total_scheduled
                END::numeric, 0::numeric) AS phone_declined_perc,
            COALESCE(cat.phone_flaked, 0::bigint) AS phone_flaked,
            COALESCE(cat.phone_flaked::numeric * 1.0 /
                CASE
                    WHEN cat.phone_total_scheduled < 1 THEN 1::bigint
                    ELSE cat.phone_total_scheduled
                END::numeric, 0::numeric) AS phone_flaked_perc,
            COALESCE(cat.flake_total, 0::bigint) AS flake_total,
            COALESCE(cat.flake_attempts, 0::bigint) AS flake_attempts,
            COALESCE(cat.flake_attempts::numeric * 1.0 /
                CASE
                    WHEN cat.flake_total < 1 THEN 1::bigint
                    ELSE cat.flake_total
                END::numeric, 0::numeric) AS flake_attempts_perc,
            COALESCE(cat.flake_rescheduled, 0::bigint) AS flake_rescheduled,
            COALESCE(cat.flake_rescheduled::numeric * 1.0 /
                CASE
                    WHEN cat.flake_total < 1 THEN 1::bigint
                    ELSE cat.flake_total
                END::numeric, 0::numeric) AS flake_rescheduled_perc,
            COALESCE(cat.flake_total - cat.flake_attempts, 0::bigint) AS flake_chase_remaining,
            COALESCE((cat.flake_total - cat.flake_attempts)::numeric * 1.0 /
                CASE
                    WHEN cat.flake_total < 1 THEN 1::bigint
                    ELSE cat.flake_total
                END::numeric, 0::numeric) AS flake_chase_remaining_perc,
            COALESCE(ct.canvassers_all_day, 0::numeric) AS canvassers_all_day,
            COALESCE(ct.actual_all_day, 0::bigint) AS actual_all_day,
            COALESCE(ct.goal_all_day, 0::bigint) AS goal_all_day,
            COALESCE(ct.packets_all_day, 0::bigint) AS packets_out_all_day,
            COALESCE(ct.actual_all_day::numeric * 1.0 /
                CASE
                    WHEN ct.canvassers_all_day < 1::numeric THEN 1::numeric
                    ELSE ct.canvassers_all_day
                END, 0::numeric) AS kps,
            COALESCE(ct.canvassers_out_now, 0::numeric) AS canvassers_out_now,
            COALESCE(ct.actual_out_now, 0::bigint) AS actual_out_now,
            COALESCE(ct.goal_out_now, 0::bigint) AS goal_out_now,
            COALESCE(ct.packets_out_now, 0::bigint) AS packets_out_now,
            COALESCE(ct.actual_out_now::numeric * 1.0 /
                CASE
                    WHEN ct.canvassers_out_now < 1::numeric THEN 1::numeric
                    ELSE ct.canvassers_out_now
                END, 0::numeric) AS kph,
            COALESCE(ct.overdue_check_in, 0::bigint) AS overdue_check_ins
           FROM {0}.location l
             LEFT JOIN confirm_attempt_totals cat ON l.locationid = cat.shift_location
             LEFT JOIN canvass_totals ct ON l.locationid = ct.shift_location
          WHERE NOT (l.region::text = ANY (ARRAY['In'::character varying::text, 'Ou'::character varying::text, 'Th'::character varying::text]))
        ), region_totals AS (
         SELECT office_totals.region,
            office_totals.region::text || ' Total'::text AS office,
            sum(office_totals.canvass_total_scheduled)::bigint AS canvass_total_scheduled,
            sum(office_totals.canvass_same_day_confirmed)::bigint AS canvass_same_day_confirmed,
            avg(office_totals.canvass_same_day_confirmed_perc) AS canvass_same_day_confirmed_perc,
            sum(office_totals.canvass_completed)::bigint AS canvass_completed,
            avg(office_totals.canvass_completed_perc) AS canvass_completed_perc,
            sum(office_totals.canvass_declined)::bigint AS canvass_declined,
            avg(office_totals.canvass_declined_perc) AS canvass_declined_perc,
            sum(office_totals.canvass_flaked)::bigint AS canvass_flaked,
            avg(office_totals.canvass_flaked_perc) AS canvass_flaked_perc,
            sum(office_totals.phone_total_scheduled)::bigint AS phone_total_scheduled,
            sum(office_totals.phone_same_day_confirmed)::bigint AS phone_same_day_confirmed,
            avg(office_totals.phone_same_day_confirmed_perc) AS phone_same_day_confirmed_perc,
            sum(office_totals.phone_completed)::bigint AS phone_completed,
            avg(office_totals.phone_completed_perc) AS phone_completed_perc,
            sum(office_totals.phone_declined)::bigint AS phone_declined,
            avg(office_totals.phone_declined_perc) AS phone_declined_perc,
            sum(office_totals.phone_flaked)::bigint AS phone_flaked,
            avg(office_totals.phone_flaked_perc) AS phone_flaked_perc,
            sum(office_totals.flake_total)::bigint AS flake_total,
            sum(office_totals.flake_attempts)::bigint AS flake_attempts,
            avg(office_totals.flake_attempts_perc) AS flake_attempts_perc,
            sum(office_totals.flake_rescheduled)::bigint AS flake_rescheduled,
            avg(office_totals.flake_rescheduled_perc) AS flake_rescheduled_perc,
            sum(office_totals.flake_chase_remaining)::bigint AS flake_chase_remaining,
            avg(office_totals.flake_chase_remaining_perc) AS flake_chase_remaining_perc,
            sum(office_totals.canvassers_all_day)::bigint AS canvassers_all_day,
            sum(office_totals.actual_all_day)::bigint AS actual_all_day,
            sum(office_totals.goal_all_day)::bigint AS goal_all_day,
            sum(office_totals.packets_out_all_day)::bigint AS packets_out_all_day,
            avg(office_totals.kps) AS kps,
            sum(office_totals.canvassers_out_now)::bigint AS canvassers_out_now,
            sum(office_totals.actual_out_now)::bigint AS actual_out_now,
            sum(office_totals.goal_out_now)::bigint AS goal_out_now,
            sum(office_totals.packets_out_now)::bigint AS packets_out_now,
            avg(office_totals.kph) AS kph,
            sum(office_totals.overdue_check_ins)::bigint AS overdue_check_ins
           FROM office_totals
          GROUP BY office_totals.region
         HAVING NOT office_totals.region::text = 'Ou'::text
        ), state_totals AS (
         SELECT 'Missouri'::text AS region,
            'State Total'::text AS office,
            sum(office_totals.canvass_total_scheduled)::bigint AS canvass_total_scheduled,
            sum(office_totals.canvass_same_day_confirmed)::bigint AS canvass_same_day_confirmed,
            avg(office_totals.canvass_same_day_confirmed_perc) AS canvass_same_day_confirmed_perc,
            sum(office_totals.canvass_completed)::bigint AS canvass_completed,
            avg(office_totals.canvass_completed_perc) AS canvass_completed_perc,
            sum(office_totals.canvass_declined)::bigint AS canvass_declined,
            avg(office_totals.canvass_declined_perc) AS canvass_declined_perc,
            sum(office_totals.canvass_flaked)::bigint AS canvass_flaked,
            avg(office_totals.canvass_flaked_perc) AS canvass_flaked_perc,
            sum(office_totals.phone_total_scheduled)::bigint AS phone_total_scheduled,
            sum(office_totals.phone_same_day_confirmed)::bigint AS phone_same_day_confirmed,
            avg(office_totals.phone_same_day_confirmed_perc) AS phone_same_day_confirmed_perc,
            sum(office_totals.phone_completed)::bigint AS phone_completed,
            avg(office_totals.phone_completed_perc) AS phone_completed_perc,
            sum(office_totals.phone_declined)::bigint AS phone_declined,
            avg(office_totals.phone_declined_perc) AS phone_declined_perc,
            sum(office_totals.phone_flaked)::bigint AS phone_flaked,
            avg(office_totals.phone_flaked_perc) AS phone_flaked_perc,
            sum(office_totals.flake_total)::bigint AS flake_total,
            sum(office_totals.flake_attempts)::bigint AS flake_attempts,
            avg(office_totals.flake_attempts_perc) AS flake_attempts_perc,
            sum(office_totals.flake_rescheduled)::bigint AS flake_rescheduled,
            avg(office_totals.flake_rescheduled_perc) AS flake_rescheduled_perc,
            sum(office_totals.flake_chase_remaining)::bigint AS flake_chase_remaining,
            avg(office_totals.flake_chase_remaining_perc) AS flake_chase_remaining_perc,
            sum(office_totals.canvassers_all_day)::bigint AS canvassers_all_day,
            sum(office_totals.actual_all_day)::bigint AS actual_all_day,
            sum(office_totals.goal_all_day)::bigint AS goal_all_day,
            sum(office_totals.packets_out_all_day)::bigint AS packets_out_all_day,
            avg(office_totals.kps) AS kps,
            sum(office_totals.canvassers_out_now)::bigint AS canvassers_out_now,
            sum(office_totals.actual_out_now)::bigint AS actual_out_now,
            sum(office_totals.goal_out_now)::bigint AS goal_out_now,
            sum(office_totals.packets_out_now)::bigint AS packets_out_now,
            avg(office_totals.kph) AS kph,
            sum(office_totals.overdue_check_ins)::bigint AS overdue_check_ins
           FROM office_totals
        )
 SELECT office_totals.region,
    office_totals.office,
    office_totals.canvass_total_scheduled,
    office_totals.canvass_same_day_confirmed,
    office_totals.canvass_same_day_confirmed_perc,
    office_totals.canvass_completed,
    office_totals.canvass_completed_perc,
    office_totals.canvass_declined,
    office_totals.canvass_declined_perc,
    office_totals.canvass_flaked,
    office_totals.canvass_flaked_perc,
    office_totals.phone_total_scheduled,
    office_totals.phone_same_day_confirmed,
    office_totals.phone_same_day_confirmed_perc,
    office_totals.phone_completed,
    office_totals.phone_completed_perc,
    office_totals.phone_declined,
    office_totals.phone_declined_perc,
    office_totals.phone_flaked,
    office_totals.phone_flaked_perc,
    office_totals.flake_total,
    office_totals.flake_attempts,
    office_totals.flake_attempts_perc,
    office_totals.flake_rescheduled,
    office_totals.flake_rescheduled_perc,
    office_totals.flake_chase_remaining,
    office_totals.flake_chase_remaining_perc,
    office_totals.canvassers_all_day,
    office_totals.actual_all_day,
    office_totals.goal_all_day,
    office_totals.packets_out_all_day,
    office_totals.kps,
    office_totals.canvassers_out_now,
    office_totals.actual_out_now,
    office_totals.goal_out_now,
    office_totals.packets_out_now,
    office_totals.kph,
    office_totals.overdue_check_ins
   FROM office_totals
UNION
 SELECT region_totals.region,
    region_totals.office,
    region_totals.canvass_total_scheduled,
    region_totals.canvass_same_day_confirmed,
    region_totals.canvass_same_day_confirmed_perc,
    region_totals.canvass_completed,
    region_totals.canvass_completed_perc,
    region_totals.canvass_declined,
    region_totals.canvass_declined_perc,
    region_totals.canvass_flaked,
    region_totals.canvass_flaked_perc,
    region_totals.phone_total_scheduled,
    region_totals.phone_same_day_confirmed,
    region_totals.phone_same_day_confirmed_perc,
    region_totals.phone_completed,
    region_totals.phone_completed_perc,
    region_totals.phone_declined,
    region_totals.phone_declined_perc,
    region_totals.phone_flaked,
    region_totals.phone_flaked_perc,
    region_totals.flake_total,
    region_totals.flake_attempts,
    region_totals.flake_attempts_perc,
    region_totals.flake_rescheduled,
    region_totals.flake_rescheduled_perc,
    region_totals.flake_chase_remaining,
    region_totals.flake_chase_remaining_perc,
    region_totals.canvassers_all_day,
    region_totals.actual_all_day,
    region_totals.goal_all_day,
    region_totals.packets_out_all_day,
    region_totals.kps,
    region_totals.canvassers_out_now,
    region_totals.actual_out_now,
    region_totals.goal_out_now,
    region_totals.packets_out_now,
    region_totals.kph,
    region_totals.overdue_check_ins
   FROM region_totals
UNION
 SELECT state_totals.region,
    state_totals.office,
    state_totals.canvass_total_scheduled,
    state_totals.canvass_same_day_confirmed,
    state_totals.canvass_same_day_confirmed_perc,
    state_totals.canvass_completed,
    state_totals.canvass_completed_perc,
    state_totals.canvass_declined,
    state_totals.canvass_declined_perc,
    state_totals.canvass_flaked,
    state_totals.canvass_flaked_perc,
    state_totals.phone_total_scheduled,
    state_totals.phone_same_day_confirmed,
    state_totals.phone_same_day_confirmed_perc,
    state_totals.phone_completed,
    state_totals.phone_completed_perc,
    state_totals.phone_declined,
    state_totals.phone_declined_perc,
    state_totals.phone_flaked,
    state_totals.phone_flaked_perc,
    state_totals.flake_total,
    state_totals.flake_attempts,
    state_totals.flake_attempts_perc,
    state_totals.flake_rescheduled,
    state_totals.flake_rescheduled_perc,
    state_totals.flake_chase_remaining,
    state_totals.flake_chase_remaining_perc,
    state_totals.canvassers_all_day,
    state_totals.actual_all_day,
    state_totals.goal_all_day,
    state_totals.packets_out_all_day,
    state_totals.kps,
    state_totals.canvassers_out_now,
    state_totals.actual_out_now,
    state_totals.goal_out_now,
    state_totals.packets_out_now,
    state_totals.kph,
    state_totals.overdue_check_ins
   FROM state_totals
  ORDER BY 1, 2;
=======
CREATE VIEW {0}.dashboard_totals AS 
WITH confirm_attempt_totals AS (
	
	SELECT l.locationname
	, SUM(CASE WHEN role = 'Canvassing' THEN 1 ELSE 0 END) canvass_total_scheduled
	, SUM(CASE WHEN role = 'Canvassing' AND s.status = 'Same Day Confirmed' THEN 1 ELSE 0 END) canvass_same_day_confirmed
	, SUM(CASE WHEN role = 'Canvassing' AND (s.status = 'Completed' OR s.status = 'In') THEN 1 ELSE 0 END) canvass_completed
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
	FROM {0}.shift s
	JOIN {0}.location l
		ON l.locationid = s.shift_location
	WHERE s.is_active = true
	GROUP BY 1
	
), canvass_group_totals AS (
	
	SELECT s.shift_location, cg.id, cg.actual, cg.goal, cg.packets_given, cg.check_in_time, cg.is_returned, cg.departure
	, COUNT(*)::bigint group_canvassers
	FROM {0}.canvass_group cg
	JOIN {0}.shift s
	ON cg.id = s.canvass_group
	WHERE cg.is_active = true
	AND s.is_active = true
	GROUP BY 1, 2
	
), canvass_totals AS (
	
	SELECT l.locationname
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
	JOIN {0}.location l
		ON l.locationid = shift_location
	GROUP BY 1
	
), locations AS (

	SELECT locationname
	FROM {0}.location
	GROUP BY locationname

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
FROM {0}.location l 
LEFT JOIN confirm_attempt_totals cat
	ON l.locationname = cat.locationname
LEFT JOIN canvass_totals ct
	ON l.locationname = ct.locationname
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


>>>>>>> 3b34b77fa7df045ef883eee58ed6612ade455990
"""




