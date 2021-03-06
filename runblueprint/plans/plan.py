import enum
import uuid


Phases = enum.Enum('Phases', 'Base Lactate Prep Taper Recovery')


class Plan():
    def __init__(self, name, weeks):
        self.name = name
        self.id = uuid.uuid1().hex
        self.weeks = weeks  # List of weeks

    def __str__(self):
        return '{} {} Week Plan'.format(self.name, len(self.weeks))

    @property
    def distance(self):
        return sum(week.distance for week in self.weeks)

    @property
    def time(self):
        return sum(x.time for x in self.weeks)

    @property
    def days(self):
        """ A handy generator of all plan days. """
        return (day for week in self.weeks for day in week.days)

    @property
    def start_date(self):
        return self.weeks[0].days[0].date

    @property
    def length(self):
        return len(self.weeks)

    def peak_week(self):
        """ Find the peak week, which is the longest by distance. """
        max_distance = 0
        peak_week = None
        for week in self.weeks:
            if week.distance >= max_distance:
                max_distance = week.distance
                peak_week = week
        return peak_week

    def get_by_title(self, title):
        """ Find a week by title, return (index, week) tuple. """
        for i, week in enumerate(self.weeks):
            if title.lower() in week.title.lower():  # Case insensitive
                return (i, week)

    def count_weeks_by_type(self, type):
        """ Count number of weeks for a given type. """
        return sum(1 for x in self.weeks if x.type == type)

    def get_weeks_by_type(self, type):
        """ Return list of (index, week) tuples of weeks of a given type. """
        return [(i, x) for i, x in enumerate(self.weeks) if x.type == type]

    def get_day_by_date(self, date):
        for week in self.weeks:
            for day in week.days:
                if day.date == date:
                    return day
