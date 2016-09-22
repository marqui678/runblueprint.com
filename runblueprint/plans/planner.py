import collections
import datetime
import logging
import math
import uuid

from dateutil.relativedelta import *
from dateutil.rrule import *
from .prototypes import weeks as weekprototypes



class Plan():
    def __init__(self, weeks):
        self.id = uuid.uuid1().hex
        self.weeks = weeks  # List of weeks

    def __str__(self):
        return 'Plan {}: {} weeks'.format(self.id, len(self.weeks))

    @property
    def distance(self):
        return sum(x.distance for x in self.weeks)

    @property
    def time(self):
        return sum(x.time for x in self.weeks)

    def get(self, title):
        """ Find a week by title, return (index, week) tuple. """
        for i, week in enumerate(self.weeks):
            if week.title.lower() == title:
                return i, week

class Week():
    WeekTypes = ('Base', 'Growth', 'Work', 'Peak', 'Taper', 'Race', 'Recovery')
    Types = collections.namedtuple('WeekTypes', WeekTypes)(*WeekTypes)  # Define constants for Week Types

    def __init__(self, number, days):
        self.number = number
        self.days = days  # List of days
        self.title = ''
        self.type = ''
        self._target_distance = 0  # Internal: planned distance for that week

    @property
    def distance(self):
        return sum(x.distance for x in self.days)

    @property
    def time(self):
        return sum(x.time for x in self.days)

    def __str__(self):
        return 'Week {}: "{}" ({}, {:.2f} km)'.format(self.number, self.title, self.type, self.distance)

class Day():
    def __init__(self, number, date):
        self.number = number
        self.date = date
        self.distance = 0
        self.time = 0
        self.type = None  # Run type, e.g. Easy, Tempo

    def __str__(self):
        return '{}. {} {}: {:.2f}'.format(self.number,
            self.date.strftime('%Y-%m-%d'),
            self.date.strftime('%a'),
            self.distance)



def generate_plan(form_data):
    plan = generate_blank_plan(form_data)

    assign_week_types(plan, form_data)
    assign_weekly_distance(plan, form_data)
    assign_daily_distance(plan)

    return plan


def assign_week_types(plan, form_data):
    # Deternmine Peak Week
    peak_day = form_data.race_date + relativedelta(weeks=-form_data.taper_length)
    for week in plan.weeks:
        for day in week.days:
            if day.date == peak_day:
                week.title = 'peak week'

    # Set Base weeks
    for week in plan.weeks:
        week.type = Week.Types.Base  # Temporarily ALL weeks are base weeks!

    # Set Recovery weeks
    for week in plan.weeks[-form_data.recovery_weeks:]:
        week.type = Week.Types.Recovery


def assign_weekly_distance(plan, form_data):
    """ Assign weekly mileage targets to each of our plan's weeks. """
    start_dist = determine_starting_mileage(form_data)  # TODO: Week 0 might be a base phase and not actually use the "starting mileage" value
    peak_dist = determine_peak_mileage(form_data)

    start_idx = 0
    peak_idx, _ = plan.get('peak week')

    logging.warn((start_dist, peak_dist, start_idx, peak_idx))
    for i, week in enumerate(plan.weeks[:peak_idx + 1]):  # Fill in from weeks 0 to peak week
        target_distance = (peak_dist - start_dist) / (peak_idx - start_idx) * i  # Linearly increase in mileage from start to peak
        week._target_distance = target_distance


def assign_daily_distance(plan):
    """ Determine daily distance through distance and prototype percent. """
    baseweekproto = weekprototypes.base_week
    restweekproto = weekprototypes.rest_week

    for week in plan.weeks:
        weekly_distance = week._target_distance
        for day in week.days:
            dayoftheweek = day.number % 7
            percent = baseweekproto[dayoftheweek]['percent_of_weekly_distance']
            day.distance = weekly_distance * percent


def determine_starting_mileage(form_data):
    """
    Starting mileage is equal to steady mileage.

    Depends on:
    * steady_mileage
    """
    starting_mileage = form_data.steady_mileage
    if starting_mileage is None:
        starting_mileage = 40
    return starting_mileage


def determine_peak_mileage(form_data):
    """
    Peak mileage is the max of 100 miles or the race_distance, whichever
    is smaller.

    Depends on:
    * race_distance
    """
    peak_mileage = max(160, form_data.race_distance)
    return peak_mileage


def generate_blank_plan(form_data):
    """
    A blank plan has all the days of training in it, including
    recovery block. But the no distances or workouts.
    """
    start_date = determine_plan_start(form_data.plan_start, form_data.week_day_start)
    end_date = add_recovery_block(form_data.race_date, form_data.recovery_weeks)
    all_dates = generate_plan_dates(start_date, end_date)
    all_days = list(Day(i, d) for i, d in enumerate(all_dates, start=1))
    all_weeks = list(Week(i, w) for i, w in enumerate(chunk_into_weeks(all_days), start=1))
    return Plan(all_weeks)


def determine_plan_start(plan_start, week_day_start):
    """
    Calculate when the plan's first day is, given that week 1 must start on
    the specified week_day_start.
    """
    delta_days = (7 - int(week_day_start) - plan_start.isoweekday()) % 7
    start_day = plan_start - datetime.timedelta(delta_days)
    return start_day


def add_recovery_block(race_date, recovery_weeks):
    return race_date + relativedelta(weeks=+recovery_weeks)


def generate_plan_dates(start, end):
    return list(d.date() for d in rrule(DAILY, dtstart=start, until=end))


def chunk_into_weeks(seq, size=7):
    """ Chunks days into week batches. """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))
