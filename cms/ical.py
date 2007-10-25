# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from Standard Library
from calendar import monthrange, isleap
from cStringIO import StringIO
from datetime import datetime, date, time, timedelta

# Import from itools
from itools.uri import Path
from itools.i18n import get_language_name
from itools.datatypes import Enumerate, Unicode, Date, DataType
from itools.handlers import Folder, Property
from itools.ical import get_grid_data, icalendar, PropertyValue, DateTime
from itools.ical import icalendarTable, Record, Time
from itools.stl import stl
from registry import register_object_class

# Import from itools.cms
from text import Text
from base import Handler
from table import Multiple, Table

resolution = timedelta.resolution

months = {1: u'January', 2: u'February', 3: u'March', 4: u'April',
          5: u'May', 6: u'June', 7: u'July', 8: u'August', 9: u'September',
          10: u'October', 11: u'November', 12: u'December'}

days = {0: u'Monday', 1: u'Tuesday', 2: u'Wednesday', 3: u'Thursday',
        4: u'Friday', 5: u'Saturday', 6: u'Sunday'}


def get_current_date(value=None):
    """
    Get date as a date object from string value.
    By default, get today's date as a date object.
    """
    if value is None:
        return date.today()
    try:
        return Date.decode(value)
    except:
        return date.today()


def build_timetables(start_time, end_time, interval):
    """
    Build a list of timetables represented as tuples(start, end).
    Interval is given by minutes.
    """
    start =  datetime(2000, 1, 1)
    if start_time:
        start = datetime.combine(start.date(), start_time)
    end =  datetime(2000, 1, 1, 23, 59)
    if end_time:
        end = datetime.combine(start.date(), end_time)

    timetables, tt_start = [], start
    while tt_start < end:
        tt_end = tt_start + timedelta(minutes=interval)
        timetables.append((tt_start.time(), tt_end.time()))
        tt_start = tt_end
    return timetables


def check_timetable_entry(context, key_start, key_end):
    """ Check if timetable built from given key value is valid or not."""
    start = context.get_form_value(key_start)
    end = context.get_form_value(key_end)
    if not start or start == '__:__' or \
       not end or end == '__:__':
        return u'Wrong time selection.'
    try:
        start = Time.decode(start)
        end = Time.decode(end)
    except:
        return u'Wrong time selection (HH:MM).'
    if start >= end:
        return u'Start time must be earlier than end time.'
    return (start, end)



class Status(Enumerate):

    options = [{'name': 'TENTATIVE', 'value': u'Tentative'},
               {'name': 'CONFIRMED', 'value': u'Confirmed'},
               {'name': 'CANCELLED', 'value': u'Cancelled'}]



class CalendarView(object):

    # Start 07:00, End 21:00, Interval 30min
    class_cal_range = (time(7,0), time(21,0), 30)
    class_cal_fields = ('SUMMARY', 'DTSTART', 'DTEND')
    class_weekly_shown = ('SUMMARY', )


    timetables = [((7,0),(8,0)), ((8,0),(9,0)), ((9,0),(10,0)),
                  ((10,0),(11,0)), ((11,0),(12,0)), ((12,0),(13,0)),
                  ((13,0),(14,0)), ((14,0),(15,0)), ((15,0),(16,0)),
                  ((16,0),(17,0)), ((17,0),(18,0)), ((18,0),(19,0)),
                  ((19,0),(20,0)), ((20,0),(21,0))]

    # default values for fields within namespace
    default_fields = {
        'UID': None, 'SUMMARY': u'', 'LOCATION': u'', 'DESCRIPTION': u'',
        'DTSTART_year': None, 'DTSTART_month': None, 'DTSTART_day': None,
        'DTSTART_hours': '', 'DTSTART_minutes': '',
        'DTEND_year': None, 'DTEND_month': None, 'DTEND_day': None,
        'DTEND_hours': '', 'DTEND_minutes': '',
        'ATTENDEE': [], 'COMMENT': [], 'STATUS': {}
      }

    # default viewed fields on monthly_view
    default_viewed_fields = ('DTSTART', 'DTEND', 'SUMMARY', 'STATUS')

    @classmethod
    def get_defaults(cls, selected_date=None, tt_start=None, tt_end=None):
        """Return a dic with default values for default fields. """

        # Default values for DTSTART and DTEND
        default = cls.default_fields.copy()

        if selected_date:
            year, month, day = selected_date.split('-')
            default['DTSTART_year'] = default['DTEND_year'] = year
            default['DTSTART_month'] = default['DTEND_month'] = month
            default['DTSTART_day'] = default['DTEND_day'] = day
        if tt_start:
            hours, minutes = Time.encode(tt_start).split(':')
            default['DTSTART_hours'] = hours
            default['DTSTART_minutes'] = minutes
        if tt_end:
            hours, minutes = Time.encode(tt_end).split(':')
            default['DTEND_hours'] = hours
            default['DTEND_minutes'] = minutes

        return default


    @classmethod
    def get_cal_range(cls):
        return cls.class_cal_range


    @classmethod
    def get_cal_fields(cls):
        return cls.class_cal_fields


    @classmethod
    def get_weekly_shown(cls):
        return cls.class_weekly_shown


    def get_first_day(self):
        """
        Returns 0 if Sunday is the first day of the week, else 1.
        For now it has to be overridden to return anything else than 1.
        """
        return 1


    def add_selector_ns(self, c_date, method, namespace):
        """
        Set header used to navigate into time.

          datetime.strftime('%U') gives week number, starting week by Sunday
          datetime.strftime('%W') gives week number, starting week by Monday
          This week number is calculated as "Week O1" begins on the first
          Sunday/Monday of the year. Its range is [0,53].

        We adjust week numbers to fit rules which are used by french people.
        XXX Check for other countries
        """
        if self.get_first_day() == 1:
            format = '%W'
        else:
            format = '%U'
        week_number = Unicode.encode(c_date.strftime(format))
        # Get day of 1st January, if < friday and != monday then number++
        day, kk = monthrange(c_date.year, 1)
        if day in (1, 2, 3):
            week_number = str(int(week_number) + 1)
            if len(week_number) == 1:
                week_number = '0%s' % week_number
        current_week = self.gettext(u'Week ') + week_number
        tmp_date = c_date - timedelta(7)
        previous_week = ";%s?date=%s" % (method, Date.encode(tmp_date))
        tmp_date = c_date + timedelta(7)
        next_week = ";%s?date=%s" % (method, Date.encode(tmp_date))
        # Month
        current_month = self.gettext(months[c_date.month])
        delta = 31
        if c_date.month != 1:
            kk, delta = monthrange(c_date.year, c_date.month - 1)
        tmp_date = c_date - timedelta(delta)
        previous_month = ";%s?date=%s" % (method, Date.encode(tmp_date))
        kk, delta = monthrange(c_date.year, c_date.month)
        tmp_date = c_date + timedelta(delta)
        next_month = ";%s?date=%s" % (method, Date.encode(tmp_date))
        # Year
        date_before = date(c_date.year, 2, 28)
        date_after = date(c_date.year, 3, 1)
        delta = 365
        if (isleap(c_date.year - 1) and c_date <= date_before) \
          or (isleap(c_date.year) and c_date > date_before):
            delta = 366
        tmp_date = c_date - timedelta(delta)
        previous_year = ";%s?date=%s" % (method, Date.encode(tmp_date))
        delta = 365
        if (isleap(c_date.year) and c_date <= date_before) \
          or (isleap(c_date.year +1) and c_date >= date_after):
            delta = 366
        tmp_date = c_date + timedelta(delta)
        next_year = ";%s?date=%s" % (method, Date.encode(tmp_date))
        # Set value into namespace
        namespace['current_week'] = current_week
        namespace['previous_week'] = previous_week
        namespace['next_week'] = next_week
        namespace['current_month'] = current_month
        namespace['previous_month'] = previous_month
        namespace['next_month'] = next_month
        namespace['current_year'] = c_date.year
        namespace['previous_year'] = previous_year
        namespace['next_year'] = next_year
        # Add today link
        tmp_date = date.today()
        namespace['today'] = ";%s?date=%s" % (method, Date.encode(tmp_date))
        return namespace


    # Get days of week based on get_first_day's result for start
    def days_of_week_ns(self, start, num=None, ndays=7, selected=None):
        """
          start : start date of the week
          num : True if we want to get number of the day too
          ndays : number of days we want
          selected : selected date
        """
        current_date = start
        ns_days = []
        for index in range(ndays):
            ns =  {}
            ns['name'] = self.gettext(days[current_date.weekday()])
            if num:
                ns['nday'] = current_date.day
            else:
                ns['nday'] = None
            if selected:
                ns['selected'] = (selected == current_date)
            else:
                ns['selected'] = None
            ns_days.append(ns)
            current_date = current_date + timedelta(1)
        return ns_days


    # Get one line with times of timetables for daily_view
    def get_header_timetables(self, timetables, delta=45):
        current_date = date.today()
        timetable = timetables[0]
        last_start = datetime.combine(current_date, timetable[0])

        ns_timetables = []
        # Add first timetable start time
        ns_timetable =  {'start': last_start.strftime('%H:%M')}
        ns_timetables.append(ns_timetable)

        # Add next ones if delta time > delta minutes
        for timetable in timetables[1:]:
            tt_start = timetable[0]
            tt_start = datetime.combine(current_date, tt_start)
            if tt_start - last_start > timedelta(minutes=delta):
                ns_timetable =  {'start': tt_start.strftime('%H:%M')}
                ns_timetables.append(ns_timetable)
                last_start = tt_start
            else:
                ns_timetables.append({'start': None})

        return ns_timetables


    # Get one line with header and empty cases with only '+' for daily_view
    def get_header_columns(self, calendar_name, args, timetables, cal_fields,
                           new_class='add_event', new_value='+'):
        ns_columns = []
        for start, end in timetables:
            start = Time.encode(start)
            end = Time.encode(end)

            tmp_args = args + '&start_time=%s' % start
            tmp_args = tmp_args + '&end_time=%s' % end
            tmp_args = tmp_args + '&id=%s/' % calendar_name
            new_url = ';edit_event_form?%s' % (tmp_args)

            column =  {'class': None,
                      'colspan': 1,
                      'rowspan': 1,
                      'DTSTART': start,
                      'DTEND': end,
                      'new_url': new_url,
                      'new_class': new_class,
                      'new_value': new_value}
            # Fields in template but not shown
            for field in cal_fields:
                if field not in column:
                    column[field] = None
            ns_columns.append(column)
        return ns_columns


    def get_timetables(self):
        """
        Build a list of timetables represented as tuples(start, end).
        Data are taken from metadata or from class value.

        Example of metadata:
          <timetables>(8,0),(10,0);(10,30),(12,0);(13,30),(17,30)</timetables>
        """
        if self.has_property('ikaaro:timetables'):
            return self.get_property('ikaaro:timetables')

        # From class value
        timetables = []
        for index, (start, end) in enumerate(self.timetables):
            timetables.append((time(start[0], start[1]), time(end[0], end[1])))
        return timetables


    # Get timetables as a list of string containing time start of each one
    def get_timetables_grid_ns(self, start_date):
        """ Build namespace to give as grid to gridlayout factory."""
        ns_timetables = []
        for calendar in self.get_calendars():
            for start, end in calendar.get_timetables():
                for value in (start, end):
                    value = Time.encode(value)
                    if value not in ns_timetables:
                        ns_timetables.append(value)
        return ns_timetables


    def get_grid_events(self, start_date, ndays=7, headers=None,
                        step=timedelta(1)):
        """ Build namespace to give as data to gridlayout factory."""
        # Get events by day
        ns_days = []
        current_date = start_date

        if headers is None:
            headers = [None] * ndays

        # For each found calendar (or self), get events
        events = []
        # Get a list of events to display on view
        end = start_date + timedelta(days=ndays)
        cal_indexes, events = self.get_events_to_display(start_date, end)
        for header in headers:
            ns_day = {}
            # Add header if given
            ns_day['header'] = header
            # Insert events
            ns_events, events = self.events_to_namespace(events, current_date,
                                                         cal_indexes)
            ns_day['events'] = ns_events
            ns_days.append(ns_day)
            current_date = current_date + step

        return ns_days


    monthly_view__access__ = 'is_allowed_to_view'
    monthly_view__label__ = u'View'
    monthly_view__sublabel__ = u'Monthly'
    def monthly_view(self, context):
        ndays = 7
        today_date = date.today()

        # Add ical css
        css = Path(self.abspath).get_pathto('/ui/ical/calendar.css')
        context.styles.append(str(css))

        # Current date
        c_date = get_current_date(context.get_form_value('date', None))
        # Save selected date
        context.set_cookie('selected_date', c_date)

        # Method
        method = context.get_cookie('method')
        if method != 'monthly_view':
            context.set_cookie('method', 'monthly_view')

        ###################################################################
        # Calculate start of previous week
        # 0 = Monday, ..., 6 = Sunday
        weekday = c_date.weekday()
        start = c_date - timedelta(7 + weekday)
        if self.get_first_day() == 0:
            start = start - timedelta(1)
        # Calculate last date to take in account as we display  5*7 = 35 days
        end = start + timedelta(35)

        ###################################################################
        # Get a list of events to display on view
        cal_indexes, events = self.get_events_to_display(start, end)

        ###################################################################
        namespace = {}
        # Add header to navigate into time
        namespace = self.add_selector_ns(c_date, 'monthly_view', namespace)
        # Get header line with days of the week
        namespace['days_of_week'] = self.days_of_week_ns(start, ndays=ndays)

        namespace['weeks'] = []
        day = start
        # 5 weeks
        for w in range(5):
            ns_week = {'days': [], 'month': u''}
            # 7 days a week
            for d in range(7):
                # day in timetable
                if d < ndays:
                    ns_day = {}
                    ns_day['nday'] = day.day
                    ns_day['selected'] = (day == today_date)
                    ns_day['url'] = self.get_action_url(day=day)
                    # Insert events
                    ns_events, events = self.events_to_namespace(events, day,
                                                                 cal_indexes)
                    ns_day['events'] = ns_events
                    ns_week['days'].append(ns_day)
                    if day.day == 1:
                        month = self.gettext(months[day.month])
                        ns_week['month'] = month
                day = day + timedelta(1)
            namespace['weeks'].append(ns_week)

        add_icon = abspath.get_pathto('/ui/images/button_add.png')
        namespace['add_icon'] = str(add_icon)

        handler = self.get_object('/ui/ical/ical_monthly_view.xml')
        return stl(handler, namespace)


    weekly_view__access__ = 'is_allowed_to_view'
    weekly_view__label__ = u'View'
    weekly_view__sublabel__ = u'Weekly'
    def weekly_view(self, context):
        ndays = 7

        # Add ical css
        abspath = Path(self.abspath)
        css = abspath.get_pathto('/ui/ical/calendar.css')
        context.styles.append(str(css))

        # Current date
        c_date = context.get_form_value('date', None)
        if not c_date:
            c_date = context.get_cookie('selected_date')
        c_date = get_current_date(c_date)
        # Save selected date
        context.set_cookie('selected_date', c_date)

        # Method
        method = context.get_cookie('method')
        if method != 'weekly_view':
            context.set_cookie('method', 'weekly_view')

        # Calculate start of current week: 0 = Monday, ..., 6 = Sunday
        weekday = c_date.weekday()
        start = c_date - timedelta(weekday)
        if self.get_first_day() == 0:
            start = start - timedelta(1)

        namespace = {}
        # Add header to navigate into time
        namespace = self.add_selector_ns(c_date, 'weekly_view' ,namespace)

        # Get icon to appear to add a new event
        add_icon = abspath.get_pathto('/ui/images/button_add.png')
        namespace['add_icon'] = str(add_icon)

        # Get header line with days of the week
        days_of_week_ns = self.days_of_week_ns(start, True, ndays, c_date)
        ns_headers = []
        for day in days_of_week_ns:
            ns_header = '%s %s' % (day['name'], day['nday'])
            # Tip: Use 'selected' for css class to highlight selected date
            ns_headers.append(ns_header)
        # Calculate timetables and events occurring for current week
        timetables = self.get_timetables_grid_ns(start)

        events = self.get_grid_events(start, headers=ns_headers)

        # Fill data with grid (timetables) and data (events for each day)
        timetable = get_grid_data(events, timetables, start)
        namespace['timetable_data'] = timetable

        handler = self.get_object('/ui/ical/ical_grid_weekly_view.xml')
        return stl(handler, namespace)


    daily_view__access__ = 'is_allowed_to_edit'
    daily_view__label__ = u'Contents'
    daily_view__sublabel__ = u'As calendar'
    def daily_view(self, context):
        raise NotImplemented


    ######################################################################
    # Public API
    ######################################################################
    def get_action_url(self, **kw):
        """ Action to call on form submission. """
        return None


    def get_calendars(self):
        """ List of sources from which taking events. """
        return []


    def get_events_to_display(self, start, end):
        """
          Get a list of events as tuples (resource_name, start, properties{})
          and a dict with all resources from whom they belong to.
        """
        resources, events = {}, []
        for index, calendar in enumerate(self.get_calendars()):
            res, evts = calendar.get_events_to_display(start, end)
            events.extend(evts)
            resources[calendar.name] = index
        events.sort(lambda x, y : cmp(x[1], y[1]))
        return resources, events


    def events_to_namespace(self, events, day, cal_indexes):
        """
        Build namespace for events occuring on current day.
        Update events, removing past ones.

        Events is a list of events where each one follows:
          (resource_name, dtstart, event)
          'event' object must have a methods:
              - get_end
              - get_ns_event.
        """
        ns_events = []
        index = 0
        while index < len(events):
            resource_name, dtstart, event = events[index]
            e_dtstart = dtstart.date()
            e_dtend = event.get_end().date()
            # Current event occurs on current date
            # event begins during current tt
            starts_on = e_dtstart == day
            # event ends during current tt
            ends_on = e_dtend == day
            # event begins before and ends after
            out_on = (e_dtstart < day and e_dtend > day)

            if starts_on or ends_on or out_on:
                cal_index = cal_indexes[resource_name]
                if len(cal_indexes.items()) < 2:
                    resource_name = None
                ns_event = event.get_ns_event(day, resource_name=resource_name,
                                              starts_on=starts_on,
                                              ends_on=ends_on, out_on=out_on)
                if resource_name is not None:
                    resource = self.get_handler(resource_name)
                else:
                    resource = self
                ns_event['url'] = resource.get_action_url(**ns_event)
                ns_event['cal'] = cal_index
                ns_events.append(ns_event)
                # Current event end on current date
                if e_dtend == day:
                    events.remove(events[index])
                    if events == []:
                        break
                else:
                    index = index + 1
            # Current event occurs only later
            elif e_dtstart > day:
                break
            else:
                index = index + 1
        return ns_events, events


    edit_event_form__access__ = 'is_allowed_to_edit'
    edit_event_form__label__ = u'Edit'
    edit_event_form__sublabel__ = u'Event'
    def edit_event_form(self, context):
        keys = context.get_form_keys()

        # Add ical css
        abspath = Path(self.abspath)
        css = abspath.get_pathto('/ui/ical/calendar.css')
        context.styles.append(str(css))
        js = abspath.get_pathto('/ui/ical/calendar.js')
        context.scripts.append(str(js))

        uid = context.get_form_value('id', None)
        # Method
        method = context.get_cookie('method') or 'monthly_view'
        goto = ';%s' % method

        # Get date to add event
        selected_date = context.get_form_value('date', None)
        if uid is None:
            if not selected_date:
                message = u'To add an event, click on + symbol from the views.'
                return context.come_back(message, goto=goto)
        else:
            # Get it as a datetime object
            if not selected_date:
                c_date = get_current_date(selected_date)
                selected_date = Date.encode(c_date)

        # Timetables
        tt_start = context.get_form_value('start_time', None)
        tt_end = context.get_form_value('end_time', None)
        if tt_start:
            tt_start = Time.decode(tt_start)
        if tt_end:
            tt_end = Time.decode(tt_end)

        # Initialization
        namespace = {}
        namespace['remove'] = None
        namespace['resources'] = namespace['resource'] = None
        properties = []
        status = Status()

        # Existant event
        resource = None
        if uid:
            resource = self
            id = uid
            if '/' in uid:
                name, id = uid.split('/')
                if not self.has_handler(name):
                    return context.come_back(u'Invalid argument.',
                                             goto=';edit_event_form', keys=keys)
                resource = self.get_handler(name)

            # UID is used to remind which resource/id is being modified
            namespace['UID'] = uid

            if id != '':
                event = resource.get_record(id)
                if not event:
                    message = u'Event not found'
                    return context.come_back(message, goto=goto)
                namespace['remove'] = True
                properties = event.get_property()
                # Get values
                for key in properties:
                    if key == 'UID':
                        continue
                    value = properties[key]
                    if isinstance(value, list):
                        namespace[key] = value
                    elif key == 'STATUS':
                        namespace['STATUS'] = value.value
                    # Split date fields into dd/mm/yyyy and hh:mm
                    elif key in ('DTSTART', 'DTEND'):
                        value, params = value.value, value.parameters
                        year, month, day = Date.encode(value).split('-')
                        namespace['%s_year' % key] = year
                        namespace['%s_month' % key] = month
                        namespace['%s_day' % key] = day
                        param = params.get('VALUE', '')
                        if not param or param != ['DATE']:
                            hours, minutes = Time.encode(value).split(':')
                            namespace['%s_hours' % key] = hours
                            namespace['%s_minutes' % key] = minutes
                        else:
                            namespace['%s_hours' % key] = ''
                            namespace['%s_minutes' % key] = ''
                    else:
                        namespace[key] = value.value
            else:
                event = None

        if not uid:
            event = None
            # Selected calendar
            ns_calendars = []
            for calendar in self.get_calendars():
                ns_calendars.append({'name': calendar.name,
                                     'value': calendar.get_title(),
                                     'selected': False})
            namespace['resources'] = ns_calendars


        # Default managed fields are :
        # SUMMARY, LOCATION, DTSTART, DTEND, DESCRIPTION,
        # STATUS ({}), ATTENDEE ([]), COMMENT ([])
        defaults = self.get_defaults(selected_date, tt_start, tt_end)
        # Set values from context or default, if not already set
        for field in defaults:
            if field not in namespace:
                if field.startswith('DTSTART_') or field.startswith('DTEND_'):
                    for attr in ('year', 'month', 'day', 'hours', 'minutes'):
                        key = 'DTSTART_%s' % attr
                        if field.startswith('DTEND_'):
                            key = 'DTEND_%s' % attr
                        value = context.get_form_value(key) or defaults[key]
                        namespace[key] = value
                # Get value from context, used when invalid input given
                elif context.has_form_value(field):
                    namespace[field] = context.get_form_value(field)
                else:
                    # Set default value in the right format
                    namespace[field] = defaults[field]
        # STATUS is an enumerate
        try:
            namespace['STATUS'] = status.get_namespace(namespace['STATUS'])
        except:
            namespace['STATUS'] = status.get_namespace('TENTATIVE')
        # Call to gettext on Status values
        for value in namespace['STATUS']:
            value['value'] = self.gettext(value['value'])

        # Show action buttons only if current user is authorized
        if resource is None:
            namespace['allowed'] = True
        else:
            namespace['allowed'] = resource.is_organizer_or_admin(context, event)
        # Set first day of week
        namespace['firstday'] = self.get_first_day()

        handler = self.get_object('/ui/ical/ical_edit_event_form.xml')
        return stl(handler, namespace)


    edit_event__access__ = 'is_allowed_to_edit'
    def edit_event(self, context):
        id = context.get_form_value('id')
        if '/' in id:
            name, id = id.split('/', 1)
        else:
            name = context.get_form_value('resource')
        if name and self.has_handler(name):
            handler = self.get_handler(name)
            return handler.__class__.edit_event(handler, context)
        return context.come_back(u'Resource not found.')


    edit_timetables_form__access__ = 'is_allowed_to_edit'
    edit_timetables_form__label__ = u'Edit'
    edit_timetables_form__sublabel__ = u'Timetables'
    def edit_timetables_form(self, context):
        # Add ical css
        css = self.get_handler('/ui/ical/calendar.css')
        context.styles.append(str(self.get_pathto(css)))

        # Initialization
        namespace = {}
        namespace['timetables'] = []

        # Show current timetables only if previously set in metadata
        if self.has_property('ikaaro:timetables'):
            timetables = self.get_property('ikaaro:timetables')
            for index, (start, end) in enumerate(timetables):
                ns = {}
                ns['index'] = index
                ns['startname'] = '%s_start' % index
                ns['endname'] = '%s_end' % index
                ns['start'] = Time.encode(start)
                ns['end'] = Time.encode(end)
                namespace['timetables'].append(ns)
        handler = self.get_handler('/ui/ical/ical_edit_timetables.xml')
        return stl(handler, namespace)


    edit_timetables__access__ = True
    def edit_timetables(self, context):
        timetables = []
        if self.has_property('ikaaro:timetables'):
            timetables = self.get_property('ikaaro:timetables')

        # Nothing to change
        if timetables == [] and not context.has_form_value('add'):
            return context.come_back(u'Nothing to change.')

        # Remove selected lines
        if context.has_form_value('remove'):
            ids = context.get_form_values('ids')
            if ids == []:
                return context.come_back(u'Nothing to remove.')
            new_timetables = []
            for index, timetable in enumerate(timetables):
                if str(index) not in ids:
                    new_timetables.append(timetable)
            message = u'Timetable(s) removed successfully.'
        else:
            new_timetables = []
            # Update timetable or just set index to next index
            for index in range(len(timetables)):
                timetable = check_timetable_entry(context, '%s_start' % index,
                                                           '%s_end' % index)
                if not isinstance(timetable, tuple):
                    return context.come_back(timetable)
                new_timetables.append(timetable)

            # Add a new timetable
            if context.has_form_value('add'):
                timetable = check_timetable_entry(context, 'new_start',
                                                           'new_end')
                if not isinstance(timetable, tuple):
                    return context.come_back(timetable)
                new_timetables.append(timetable)

            new_timetables.sort()
            message = u'Timetables updated successfully.'

        self.set_property('ikaaro:timetables', tuple(new_timetables))
        return context.come_back(message=message)



class CalendarAware(CalendarView):

    def get_calendars(self, types=None):
        """ List of sources from which taking events. """
        if not types:
            types = (Calendar, CalendarTable)
        if isinstance(self, Folder):
            calendars = []
            for cc in types:
                calendars.extend(list(self.search_handlers(handler_class=cc)))
            return calendars
        return [self]


    # Get namespace for a resource's lines into daily_view
    def get_ns_calendar(self, calendar, c_date, cal_fields, shown_fields,
                        timetables, method='daily_view', show_conflicts=False):
        calendar_name = calendar.name
        args = 'date=%s&method=%s' % (Date.encode(c_date), method)
        new_url = ';edit_event_form?%s' % args

        ns_calendar = {}
        ns_calendar['name'] = calendar.get_title()

        ###############################################################
        # Get a dict for each event with shown_fields, tt_start, tt_end,
        # uid and colspan ; the result is a list sorted by tt_start
        events_list = calendar.search_events_in_date(c_date)
        # Get dict from events_list and sort events by start date
        ns_events = []
        for event in events_list:
            ns_event = {}
            for field in shown_fields:
                ns_event[field] = event.get_property(field).value
            event_start = event.get_property('DTSTART').value
            event_end = event.get_property('DTEND').value
            # Add timetables info
            tt_start = 0
            tt_end = len(timetables)-1
            for tt_index, (start, end) in enumerate(timetables):
                start = datetime.combine(c_date, start)
                end = datetime.combine(c_date, end)
                if start <= event_start:
                    tt_start = tt_index
                if end >= event_end:
                    tt_end = tt_index
                    break
            ns_event['tt_start'] = tt_start
            ns_event['tt_end'] = tt_end
            uid = getattr(event, 'id', getattr(event, 'uid', None))
            if calendar_name and uid:
                uid = '%s/%s' % (calendar_name, uid)
            ns_event['UID'] = uid
            ns_event['colspan'] = tt_end - tt_start + 1
            ns_events.append(ns_event)
        ns_events.sort(lambda x, y: cmp(x['tt_start'], y['tt_start']))
        ###############################################################

        # Get conflicts in events if activated
        if show_conflicts:
            conflicts = calendar.get_conflicts(c_date)
            conflicts_list = set()
            if conflicts:
                [conflicts_list.update(uids) for uids in conflicts]

        ###############################################################
        # Organize events in rows
        rows = []
        for index in range(len(timetables)):
            row_index = 0
            # Search events in current timetable
            for event in ns_events:
                if index >= event['tt_start'] and index <= event['tt_end']:
                    if index == event['tt_start']:
                        if rows == [] or row_index >= len(rows):
                            rows.append({'events': []})
                        rows[row_index]['events'].append(event)
                    row_index = row_index + 1

        ###############################################################
        # Set event values
        new_class = 'add_event'
        new_value = '+'

        ns_rows = []
        for row in rows:
            ns_row = {}
            ns_columns = []
            events = row['events']
            if events == []:
                ns_rows = None
                break
            event = events[0]
            colspan = 0

            for tt_index, (start, end) in enumerate(timetables):
                if colspan > 0:
                    colspan = colspan - 1
                    continue
                start = Time.encode(start)
                end = Time.encode(end)
                tmp_args = args + '&start_time=' + start
                tmp_args = tmp_args + '&end_time=' + end
                new_url = ';edit_event_form?%s' % (tmp_args)
                # Init column
                column =  {'class': None,
                          'colspan': 1,
                          'rowspan': 1,
                          'evt_url': None,
                          'evt_value': '>>',
                          'new_url': new_url,
                          'new_class': new_class,
                          'new_value': new_value}
                # Add event
                if event and tt_index == event['tt_start']:
                    uid = event['UID']
                    event_params = '%s&id=%s' % (args, uid)
                    go_url = ';edit_event_form?%s' % event_params
                    if show_conflicts and uid in conflicts_list:
                        css_class = 'cal_conflict'
                    else:
                        css_class = 'cal_busy'

                    column['class'] = css_class
                    column['colspan'] = event['colspan']
                    column['evt_url'] = go_url
                    column['new_url'] = None
                    column['evt_value'] = '>>'

                    # Fields to show
                    for field in shown_fields:
                        value = event[field]
                        if isinstance(value, datetime):
                            value = value.strftime('%H:%M')
                        column[field] = value

                    # Set colspan
                    colspan = event['colspan'] - 1

                    # Delete added event
                    del events[0]
                    event = None
                    if events != []:
                        event = events[0]

                # Fields in template but not shown
                for field in cal_fields:
                    if field not in column:
                        column[field] = None
                ns_columns.append(column)
                ns_row['columns'] = ns_columns
            ns_rows.append(ns_row)

        # Add ns_rows to namespace
        ns_calendar['rows'] = ns_rows

        # Add one line with header and empty cases with only '+'
        header_columns = self.get_header_columns(calendar_name, args,
                                                 timetables, cal_fields)
        ns_calendar['header_columns'] = header_columns

        # Add url to calendar keeping args
        ns_calendar['url'] = ';monthly_view?%s' % args
        ns_calendar['rowspan'] = len(rows) + 1

        return ns_calendar


    daily_view__access__ = 'is_allowed_to_edit'
    daily_view__label__ = u'Contents'
    daily_view__sublabel__ = u'As calendar'
    def daily_view(self, context):
        # Add ical css
        css = self.get_handler('/ui/ical/calendar.css')
        context.styles.append(str(self.get_pathto(css)))

        method = context.get_cookie('method')
        if method != 'daily_view':
            context.set_cookie('method', 'daily_view')

        # Current date
        selected_date = context.get_form_value('date', None)
        c_date = get_current_date(selected_date)
        selected_date = Date.encode(c_date)

        # Get fields and fields to show
        cal_fields = self.get_cal_fields()
        shown_fields = self.get_weekly_shown()

        namespace = {}
        # Add date selector
        namespace['date'] = selected_date
        namespace['firstday'] = self.get_first_day()
        namespace['link_on_summary'] = True

        # Add a header line with start time of each timetable
        start, end, interval = self.get_cal_range()
        timetables = build_timetables(start, end, interval)
        namespace['header_timetables'] = self.get_header_timetables(timetables)

        # For each found calendar
        ns_calendars = []
        for calendar in self.get_calendars():
            ns_calendar = self.get_ns_calendar(calendar, c_date, cal_fields,
                                               shown_fields, timetables)
            ns_calendars.append(ns_calendar)
        namespace['calendars'] = ns_calendars

        handler = self.get_handler('/ui/ical/daily_view.xml')
        return stl(handler, namespace)



class Calendar(Text, CalendarView, icalendar):

    class_id = 'calendar'
    class_version = '20060720'
    class_title = u'Calendar'
    class_description = u'Schedule your time with calendar files.'
    class_icon16 = 'images/icalendar16.png'
    class_icon48 = 'images/icalendar48.png'

    class_views = [['monthly_view', 'weekly_view', 'download_form'],
                   ['upload_form', 'edit_timetables_form',
                    'edit_metadata_form', 'edit_event_form']]

    def get_action_url(self, **kw):
        url = ';edit_event_form'
        params = []
        if 'day' in kw:
            params.append('date=%s' % Date.encode(kw['day']))
        if 'id' in kw:
            params.append('id=%s' % kw['id'])
        if params != []:
            url = '%s?%s' % (url, '&'.join(params))
        return url


    def get_calendars(self):
        return [self]


    def get_events_to_display(self, start, end):
        events = []
        for event in self.search_events_in_range(start, end, sortby='date'):
            e_dtstart = event.get_property('DTSTART').value
            events.append((self.name, e_dtstart, event))
        events.sort(lambda x, y : cmp(x[1], y[1]))
        return {self.name: 0}, events


    # Test if user in context is the organizer of a given event (or is admin)
    def is_organizer_or_admin(self, context, event):
        if self.get_access_control().is_admin(context.user, self):
            return True
        if event:
            organizer = event.get_property_values('ORGANIZER')
            return organizer and context.user.get_abspath() == organizer.value
        ac = self.parent.get_access_control()
        return ac.is_allowed_to_edit(context.user, self.parent)


    #######################################################################
    # User interface
    #######################################################################

    edit_metadata_form__sublabel__ = u'Metadata'

    download_form__access__ = 'is_allowed_to_view'
    download_form__sublabel__ = u'Export in ical format'


    GET__mtime__ = None
    def GET(self, context):
        return Handler.GET(self, context)


    # View
    text_view__access__ = 'is_allowed_to_edit'
    text_view__label__ = u'Text view'
    text_view__sublabel__ = u'Text view'
    def text_view(self, context):
        return '<pre>%s</pre>' % self.to_str()


    remove__access__ = 'is_allowed_to_edit'
    def remove(self, context):
        method = context.get_cookie('method') or 'monthly_view'
        goto = ';%s?%s' % (method, get_current_date())
        if method not in dir(self):
            goto = '../;%s?%s' % (method, get_current_date())

        uid = context.get_form_value('id')
        if '/' in uid:
            kk, uid = uid.split('/', 1)
        if not uid:
            return context.come_back('', goto)
        icalendar.remove(self, uid)
        return context.come_back(u'Event definitely deleted.', goto=goto)


    edit_event__access__ = 'is_allowed_to_edit'
    def edit_event(self, context):
        # Keys to keep from url
        keys = context.get_form_keys()

        # Method
        method = context.get_cookie('method') or 'monthly_view'
        goto = ';%s' % method
##        if method not in dir(self):
##            goto = '../;%s' % method

        # Get event id
        uid = context.get_form_value('id') or ''
        if '/' in uid:
            name, uid = uid.split('/', 1)

        if context.has_form_value('remove'):
            return self.remove(context)

        # Get selected_date from the 3 fields 'dd','mm','yyyy' into 'yyyy/mm/dd'
        v_items = []
        for item in ('year', 'month', 'day'):
            v_items.append(context.get_form_value('DTSTART_%s' % item))
        selected_date = '-'.join(v_items)

##        # Keys to keep from url
##        keys = ['resource']

        # Cancel
        if context.has_form_value('cancel'):
            return context.come_back('', goto, keys=keys)

        # Get id and Record object
        properties = {}
        if uid:
            event = self.get_record(uid)
            # Test if current user is admin or organizer of this event
            if not self.is_organizer_or_admin(context, event):
                message = u'You are not authorized to modify this event.'
                return context.come_back(goto, message, keys=keys)
        else:
            # Add user as Organizer
            organizer = context.user.get_abspath()
            properties['ORGANIZER'] = PropertyValue(organizer)

        for key in context.get_form_keys():
            if key in ('id', 'update', 'resource'):
                continue
            # Get date and time for DTSTART and DTEND
            if key.startswith('DTSTART_day'):
                values = {}
                for real_key in ('DTSTART', 'DTEND'):
                    # Get date
                    v_items = []
                    for item in ('year', 'month', 'day'):
                        item = '%s_%s' % (real_key, item)
                        v_item = context.get_form_value(item)
                        v_items.append(v_item)
                    v_date = '-'.join(v_items)
                    # Get time
                    hours = context.get_form_value('%s_hours' % real_key)
                    minutes = context.get_form_value('%s_minutes' % real_key)
                    params = {}
                    if hours is '':
                        value = v_date
                        params['VALUE'] = ['DATE']
                    else:
                        if minutes is '':
                            minutes = 0
                        v_time = '%s:%s' % (hours, minutes)
                        value = ' '.join([v_date, v_time])
                    # Get value as a datetime object
                    try:
                        value = DateTime.from_str(value)
                    except:
                        goto = ';edit_event_form?date=%s' % selected_date
                        message = u'One or more field is invalid.'
                        return context.come_back(goto=goto, message=message)
                    values[real_key] = value, params
                # Check if start <= end
                if values['DTSTART'][0] > values['DTEND'][0]:
                    message = u'Start date MUST be earlier than end date.'
                    goto = ';edit_event_form?date=%s' % \
                                             Date.encode(values['DTSTART'][0])
                    if uid:
                        goto = goto + '&uid=%s' % uid
                    elif context.has_form_value('timetable'):
                        timetable = context.get_form_value('timetable', 0)
                        goto = goto + '&timetable=%s' % timetable
                    return context.come_back(goto=goto, message=message)
                # Save values
                for key in ('DTSTART', 'DTEND'):
                    if key == 'DTEND' and 'VALUE' in values[key][1]:
                        value = values[key][0] + timedelta(days=1) - resolution
                        value = PropertyValue(value, **values[key][1])
                    else:
                        value = PropertyValue(values[key][0], **values[key][1])
                    properties[key] = value
            elif key.startswith('DTSTART') or key.startswith('DTEND'):
                continue
            else:
                datatype = self.get_datatype(key)
                values = context.get_form_values(key)
                if key == 'SUMMARY' and not values[0]:
                    return context.come_back(u'Summary must be filled.', goto)

                decoded_values = []
                for value in values:
                    value = datatype.decode(value)
                    decoded_values.append(PropertyValue(value))

                if datatype.occurs == 1:
                    properties[key] = decoded_values[0]
                else:
                    properties[key] = decoded_values

        if uid:
            self.update_component(uid, **properties)
        else:
            self.add_component('VEVENT', **properties)

        goto = '%s?date=%s' % (goto, selected_date)
        return context.come_back(u'Data updated', goto=goto, keys=keys)


register_object_class(Calendar)
register_object_class(icalendar, format='text/calendar')



class CalendarTable(Table, CalendarView, icalendarTable):

    class_id = 'calendarTable'
    class_version = '20060720'
    class_title = u'CalendarTable'
    class_description = u'Schedule your time with calendar files.'
    class_icon16 = 'images/icalendar16.png'
    class_icon48 = 'images/icalendar48.png'
    class_views = [['monthly_view', 'weekly_view', 'download_form'],
                   ['upload_form', 'edit_timetables_form',
                    'edit_metadata_form', 'edit_event_form']]

    record_class = Record


    GET__mtime__ = None
    def GET(self, context):
        return Handler.GET(self, context)


    # Test if user in context is the organizer of a given event (or is admin)
    def is_organizer_or_admin(self, context, event):
        if self.get_access_control().is_admin(context.user, self):
            return True
        if event:
            organizer = event.get_property('ORGANIZER')
            return organizer and context.user.get_abspath() == organizer.value
        ac = self.parent.get_access_control()
        return ac.is_allowed_to_edit(context.user, self.parent)


    def get_record(self, id):
        return icalendarTable.get_record(self, int(id))


    def edit_record(self, context):
        # check form
        check_fields = []
        for name, kk in self.get_fields():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                datatype = Multiple(type=datatype)
            check_fields.append((name, getattr(datatype, 'mandatory', False),
                                 datatype))

        error = context.check_form_input(check_fields)
        if error is not None:
            return context.come_back(error, keep=context.get_form_keys())

        # Get the record
        id = context.get_form_value('id', type=Integer)
        record = {}
        for name, title in self.get_fields():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                if is_datatype(datatype, Enumerate):
                    value = context.get_form_values(name)
                else: # textarea -> string
                    values = context.get_form_value(name)
                    values = values.splitlines()
                    value = []
                    for index in range(len(values)):
                        tmp = values[index].strip()
                        if tmp:
                            value.append(datatype.decode(tmp))
            else:
                value = context.get_form_value(name, type=datatype)
            record[name] = value

        self.update_record(id, **record)
        self.set_changed()
        goto = context.uri.resolve2('../;edit_record_form')
        return context.come_back(MSG_CHANGES_SAVED, goto=goto, keep=['id'])


    upload_form__sublabel__ = u'Upload from an ical file'
    def upload(self, context):
        file = context.get_form_value('file')

        if file is None:
            return context.come_back(u'No file has been entered.')

        # Check wether the handler is able to deal with the uploaded file
        filename, mimetype, data = file
        self.set_changed()
        try:
            self._load_state_from_ical_file(StringIO(data))
        except:
            message = (u'Upload failed: either the file does not match this'
                       u' document type ($mimetype) or it contains errors.')
            return context.come_back(message, mimetype=self.get_mimetype())

        return context.come_back(u'Version uploaded.')


    def download_form(self, context):
        namespace = {}
        namespace['url'] = '../%s/;download' % self.name
        namespace['title_or_name'] = self.get_title()
        handler = self.get_handler('/ui/file/download_form.xml')
        return stl(handler, namespace)


    def download(self, context):
        response = context.response
        response.set_header('Content-Type', 'calendar')
        return self.to_ical()


    #######################################################################
    # API related to CalendarView
    #######################################################################

    def get_action_url(self, **kw):
        url = ';edit_event_form'
        params = []
        if 'day' in kw:
            params.append('date=%s' % Date.encode(kw['day']))
        if 'id' in kw:
            params.append('id=%s' % kw['id'])
        if params != []:
            url = '%s?%s' % (url, '&'.join(params))
        return url


    def get_calendars(self):
        return [self]


    def get_events_to_display(self, start, end):
        events = []
        for event in self.search_events_in_range(start, end, sortby='date'):
            e_dtstart = event.get_property('DTSTART').value
            events.append((self.name, e_dtstart, event))
        events.sort(lambda x, y : cmp(x[1], y[1]))
        return {self.name: 0}, events


    edit_record__access__ = 'is_allowed_to_edit'
    edit_event__access__ = 'is_allowed_to_edit'
    def edit_event(self, context):
        # Keys to keep from url
        keys = context.get_form_keys()

        # Method
        method = context.get_cookie('method') or 'monthly_view'
        goto = ';%s' % method
##        if method not in dir(self):
##            goto = '../;%s' % method

        # Get event id
        uid = context.get_form_value('id') or ''
        if '/' in uid:
            name, uid = uid.split('/', 1)

        if context.has_form_value('remove'):
            return self.remove(context)

        # Get selected_date from the 3 fields 'dd','mm','yyyy' into 'yyyy/mm/dd'
        v_items = []
        for item in ('year', 'month', 'day'):
            v_items.append(context.get_form_value('DTSTART_%s' % item))
        selected_date = '-'.join(v_items)

##        # Keys to keep from url
##        keys = ['resource']

        # Cancel
        if context.has_form_value('cancel'):
            return context.come_back('', goto, keys=keys)

        # Get id and Record object
        properties = {}
        if uid:
            uid = int(uid)
            event = self.get_record(uid)
            # Test if current user is admin or organizer of this event
            if not self.is_organizer_or_admin(context, event):
                message = u'You are not authorized to modify this event.'
                return context.come_back(goto, message, keys=keys)
        else:
            # Add user as Organizer
            organizer = context.user.get_abspath()
            properties['ORGANIZER'] = Property(organizer)

        for key in context.get_form_keys():
            if key in ('id', 'update', 'resource'):
                continue
            # Get date and time for DTSTART and DTEND
            if key.startswith('DTSTART_day'):
                values = {}
                for real_key in ('DTSTART', 'DTEND'):
                    # Get date
                    v_items = []
                    for item in ('year', 'month', 'day'):
                        item = '%s_%s' % (real_key, item)
                        v_item = context.get_form_value(item)
                        v_items.append(v_item)
                    v_date = '-'.join(v_items)
                    # Get time
                    hours = context.get_form_value('%s_hours' % real_key)
                    minutes = context.get_form_value('%s_minutes' % real_key)
                    params = {}
                    if hours is '':
                        value = v_date
                        params['VALUE'] = ['DATE']
                    else:
                        if minutes is '':
                            minutes = 0
                        v_time = '%s:%s' % (hours, minutes)
                        value = ' '.join([v_date, v_time])
                    # Get value as a datetime object
                    try:
                        value = DateTime.from_str(value)
                    except:
                        goto = ';edit_event_form?date=%s' % selected_date
                        message = u'One or more field is invalid.'
                        return context.come_back(goto=goto, message=message)
                    values[real_key] = value, params
                # Check if start <= end
                if values['DTSTART'][0] > values['DTEND'][0]:
                    message = u'Start date MUST be earlier than end date.'
                    goto = ';edit_event_form?date=%s' % \
                                             Date.encode(values['DTSTART'][0])
                    if uid:
                        goto = goto + '&uid=%s' % uid
                    elif context.has_form_value('timetable'):
                        timetable = context.get_form_value('timetable', 0)
                        goto = goto + '&timetable=%s' % timetable
                    return context.come_back(goto=goto, message=message)
                # Save values
                for key in ('DTSTART', 'DTEND'):
                    if key == 'DTEND' and 'VALUE' in values[key][1]:
                        value = values[key][0] + timedelta(days=1) - resolution
                        value = Property(value, values[key][1])
                    else:
                        value = Property(values[key][0], values[key][1])
                    properties[key] = value
            elif key.startswith('DTSTART') or key.startswith('DTEND'):
                continue
            else:
                check_fields = []
                datatype = self.get_datatype(key)
                multiple = getattr(datatype, 'multiple', False) is True
                if multiple:
                    datatype = Multiple(type=datatype)
                check_fields.append((key, getattr(datatype,
                                              'mandatory', False), datatype))
                # XXX Check inputs
                error = context.check_form_input(check_fields)
                if error is not None:
                    return context.come_back(error, keep=context.get_form_keys())
                if multiple:
                    values = context.get_form_values(key)
                    decoded_values = []
                    for value in values:
                        value = datatype.decode(value)
                        decoded_values.append(Property(value))
                    values = decoded_values
                else:
                    values = context.get_form_value(key)
                    values = datatype.decode(values)
                properties[key] = values

        if uid:
            self.update_record(uid, **properties)
        else:
            properties['type'] = 'VEVENT'
            self.add_record(properties)

        goto = '%s?date=%s' % (goto, selected_date)
        return context.come_back(u'Data updated', goto=goto, keys=keys)

register_object_class(CalendarTable)
