# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Nicolas Deram <nderam@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from Standard Library
from calendar import monthrange, isleap
from datetime import datetime, date, time, timedelta

# Import from itools
from itools import i18n
from itools.datatypes import Enumerate, Unicode, Time as iTime
from itools.datatypes.datetime_ import ISOCalendarDate as Date
from itools.ical import gridlayout
from itools.ical.icalendar import icalendar, Component, PropertyValue
from itools.ical.types import data_properties, DateTime
from itools.stl import stl
from itools.web import get_context
from File import File
from registry import register_object_class

# Import from itools.cms
from itools.cms.text import Text
from itools.cms.Handler import Handler


class Status(Enumerate):

    options = [{'name': 'TENTATIVE', 'value': u'TENTATIVE'},
               {'name': 'CONFIRMED', 'value': u'CONFIRMED'}, 
               {'name': 'CANCELLED', 'value': u'CANCELLED'}]



class Time(iTime):

    @staticmethod
    def encode(value, seconds=False):
        if value is None: 
            return ''
        if not seconds: 
            return value.strftime('%H:%M')
        return value.strftime('%H:%M:%S')



class Calendar(Text, icalendar):

    class_id = 'calendar'
    class_version = '20060720'
    class_title = u'Calendar'
    class_description = u'Schedule your time with calendar files.'
    class_icon16 = 'images/icalendar16.png'
    class_icon48 = 'images/icalendar48.png'

    class_views = [['monthly_view', 'weekly_view', 'download_form'],
                   ['upload_form', 'edit_timetables_form',
                    'edit_metadata_form', 'edit_event_form']]

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

    months = {1: u'January', 2: u'February', 3: u'March', 4: u'April', 
              5: u'May', 6: u'June', 7: u'July', 8: u'August', 9: u'September',
              10: u'October', 11: u'November', 12: u'December'}

    days = {0: u'Monday', 1: u'Tuesday', 2: u'Wednesday', 3: u'Thursday', 
            4: u'Friday', 5: u'Saturday', 6: u'Sunday'}

    # class_timetables
    class_timetables = (((7,0),(8,0)), ((8,0),(9,0)), ((9,0),(10,0)), 
                        ((10,0),(11,0)), ((11,0),(12,0)), ((12,0),(13,0)), 
                        ((13,0),(14,0)), ((14,0),(15,0)), ((15,0),(16,0)), 
                        ((16,0),(17,0)), ((17,0),(18,0)), ((18,0),(19,0)), 
                        ((19,0),(20,0)), ((20,0),(21,0)))


    @classmethod
    def new_instance_form(cls, name=''):
        context = get_context()
        root = context.root

        namespace = {}
        namespace['name'] = name
        # The class id
        namespace['class_id'] = cls.class_id
        # Languages
        languages = []
        website_languages = root.get_property('ikaaro:website_languages')
        default_language = website_languages[0]
        for code in website_languages:
            language_name = i18n.get_language_name(code)
            languages.append({'code': code,
                              'name': cls.gettext(language_name),
                              'isdefault': code == default_language})
        namespace['languages'] = languages

        handler = root.get_handler('ui/Text_new_instance.xml')
        return stl(handler, namespace)


    def to_str(self):
        return icalendar.to_str(self)


    def to_text(self):
        return self.to_str()


    @classmethod
    def get_current_date(cls, value=None):
        """
        Get date as a date object from string value.
        By default, get today's date as a date object.
        """
        try:
            return Date.decode(value or date.today())
        except:
            return date.today()


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
    def add_selector_ns(cls, c_date, method, namespace):
        """
        Set header used to navigate into time.

          datetime.strftime('%U') gives week number, starting week by Sunday
          datetime.strftime('%W') gives week number, starting week by Monday
          This week number is calculated as "Week O1" begins on the first
          Sunday/Monday of the year. Its range is [0,53]. 

        We adjust week numbers to fit rules which are used by french people.
        XXX Check for other countries
        """
        format = '%W' if cls.get_first_day() == 1 else '%U'
        week_number = Unicode.encode(c_date.strftime(format))
        # Get day of 1st January, if < friday and != monday then number++
        day, xxx = monthrange(c_date.year, 1)
        if day in (1,2,3):
            week_number = str(int(week_number) + 1)
            if len(week_number) == 1:
                week_number = '0%s' % week_number
        current_week = cls.gettext(u'Week ') + week_number
        tmp_date = c_date - timedelta(7)
        previous_week = ";%s?date=%s" % (method, Date.encode(tmp_date))
        tmp_date = c_date + timedelta(7)
        next_week = ";%s?date=%s" % (method, Date.encode(tmp_date))
        # Month
        current_month = cls.gettext(cls.months[c_date.month])
        delta = 31
        if c_date.month != 1:
            xxx, delta = monthrange(c_date.year, c_date.month - 1)
        tmp_date = c_date - timedelta(delta)
        previous_month = ";%s?date=%s" % (method, Date.encode(tmp_date))
        xxx, delta = monthrange(c_date.year, c_date.month)
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


    # Test if user in context is the organizer of a given event (or is admin)
    def is_organizer_or_admin(self, context, event):
        if self.get_access_control().is_admin(context.user, event):
            return True
        if event:
            organizer = event.get_property_values('ORGANIZER')
            return organizer and context.user.get_abspath() == organizer.value
        ac = self.parent.get_access_control()
        return ac.is_allowed_to_edit(context.user, self.parent)


    # 0 means Sunday, 1 means Monday
    @classmethod
    def get_first_day(cls):
        return 1


    def get_timetables(self):
        """
        Get timetables as a list of dict with keys (index, start, end).
        Search into metadata or into class_timetables if nothing in metadata.
        """
        timetables = []
        src_timetables = self.get_property('timetables')

        # Nothing in file, so get from class variable (tuple)
        if not src_timetables:
            src_timetables = self.class_timetables
            for index, timetable in enumerate(src_timetables):
                start, end = timetable
                start = time(start[0], start[1])
                end = time(end[0], end[1])
                ns_timetable = {}
                ns_timetable['index'] = index 
                ns_timetable['start'] = start
                ns_timetable['end'] = end
                timetables.append(ns_timetable)
            return timetables

        # From file
        for index, timetable in enumerate(src_timetables.split(';')):
            ns_timetable = {}
            ns_timetable['index'] = index 
            start, end = timetable.split('),(')
            start, end = start[1:], end[:-1]
            hours, minutes = start.split(',')
            hours, minutes = int(hours), int(minutes)
            ns_timetable['start'] = time(hours, minutes)
            hours, minutes = end.split(',')
            hours, minutes = int(hours), int(minutes)
            ns_timetable['end'] = time(hours, minutes)
            timetables.append(ns_timetable)
        return timetables


    # Get timetable as dict from its index (used in projects)
    def get_timetable_by_index(self, index):
        timetable = self.get_timetables()
        if timetable:
            return timetable[index]
        return None


    # XXX DEPRECATED, not completely replaced yet
    def get_ns_events(self, selected_date, shown_fields, timetables):
        # Get list of all events
        events_list = self.search_events_in_date(selected_date)
        # Get dict from events_list and sort events by start date
        ns_events = []
        for event in events_list:
            ns_event = {}
            for field in shown_fields:
                ns_event[field] = event.get_property_values(field).value
            event_start = event.get_property_values('DTSTART').value
            event_end = event.get_property_values('DTEND').value
            # Add timetables info
            tt_start = 0
            tt_end = len(timetables)-1
            for tt_index, tt in enumerate(timetables):
                start = datetime.combine(selected_date, tt['start'])
                end = datetime.combine(selected_date, tt['end'])
                if start <= event_start:
                    tt_start = tt_index
                if end >= event_end:
                    tt_end = tt_index
                    break
            ns_event['tt_start'] = tt_start
            ns_event['tt_end'] = tt_end
            ns_event['UID'] = event.get_property_values('UID').value
            ns_event['colspan'] = tt_end - tt_start + 1
            ns_events.append(ns_event)
        ns_events.sort(lambda x, y: cmp(x['tt_start'], y['tt_start']))
        return ns_events


    # Get days of week based on get_first_day's result 
    @classmethod
    def days_of_week_ns(cls, start, num=None, ndays=7, selected=None):
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
            ns['name'] = cls.gettext(cls.days[current_date.weekday()])
            ns['nday'] = current_date.day if num else None
            ns['selected'] = (selected == current_date) if selected else None
            ns_days.append(ns)
            current_date = current_date + timedelta(1)
        return ns_days


    #########################################################################
    # Get timetables as a list of string containing time start of each one
    def get_timetables_grid_ns(self, start_date):
        """ Build namespace to give as grid to gridlayout factory."""
        timetables = self.get_timetables()

        ns_timetables = []
        for timetable in timetables:
            ns_timetables.append(Time.encode(timetable['start']))
        if ns_timetables != []:
            ns_timetables.append(Time.encode(timetables[-1]['end']))

        return ns_timetables


    def get_grid_events(self, start_date, resource_name=None, ndays=7,
                        headers=None, step=timedelta(1)):
        """ Build namespace to give as data to gridlayout factory."""
        # Get events by day
        ns_days = []
        current_date = start_date

        if headers is None:
            headers = [None] * ndays

        for header in headers:
            ns_day = {}
            # Add header if given
            ns_day['header'] = header

            # Add each event by day
            ns_events = []
            for event in self.search_events_in_date(current_date, 
                                                    sortby='date'):
                ns_event = self.get_grid_ns_event(current_date, event,
                                                  resource_name=resource_name)
                ns_events.append(ns_event)
            ns_day['events'] = ns_events

            ns_days.append(ns_day)
            current_date = current_date + step

        return ns_days


    #######################################################################
    # User interface
    #######################################################################

    edit_metadata_form__sublabel__ = u'Metadata'

    download_form__access__ = 'is_allowed_to_view'
    download_form__sublabel__ = u'Export in ical format'


    # View
    text_view__access__ = 'is_allowed_to_edit'
    text_view__label__ = u'Text view'
    text_view__sublabel__ = u'Text view'
    def text_view(self, context):
        return '<pre>%s</pre>' % self.to_str()


    def get_ns_event(self, day, event, resource_name=None, conflicts_list=[],
                     timetable=None ,starts_on=True, ends_on=True, out_on=True):
        """
        Specify the namespace given on views to represent an event.

        day: date selected XXX not used for now
        event: event selected
        resource_name: specify the resource for browse_calendar
        conflicts_list: list of conflicts for current resource, [] if not used
        timetable: timetable index

        By default, we get:

          DTSTART: HH:MM, DTEND: HH:MM, TIME: True
            or
          DTSTART: '', DTEND: '', TIME: False
  
          SUMMARY: 'summary of the event'
          STATUS: 'status' (class: cal_conflict, if uid in conflicts_list)
          ORGANIZER: 'organizer of the event'

          url: url to access edit_event_form on current event
        """
        properties = event.get_property_values
        ns = {}
        ns['SUMMARY'] = properties('SUMMARY').value
        ns['ORGANIZER'] = properties('ORGANIZER').value

        ###############################################################
        # Set dtstart and dtend values using '...' for events which 
        # appear into more than one cell
        ns['TIME'] = None
        ns['DTSTART'] = Time.encode(properties('DTSTART').value.time())
        ns['DTEND'] = Time.encode(properties('DTEND').value.time())

        if not out_on:
            dtstart = properties('DTSTART')
            dtstart, param = dtstart.value, dtstart.parameters
            if not param or 'DATE' not in param['VALUE']:
                value = ''
                if starts_on:
                    value = ns['DTSTART']
                    if ends_on:
                        value = value + '-'
                    else:
                        value = value + '...' 
                if ends_on:
                    value = value + ns['DTEND']
                    if not starts_on:
                        value = '...' + value
                ns['TIME'] = '(' + value + ')'
                
        ###############################################################
        # Set class for conflicting events or just from status value
        uid = event.uid
        if uid in conflicts_list:
            ns['STATUS'] = 'cal_conflict'
        else:
            status = properties('STATUS')
            if status:
                ns['STATUS'] = properties('STATUS').value
            else:
                ns['STATUS'] = ''

        ###############################################################
        # Set url to edit_event_form
        ns['UID'] = '%s' % uid
        url = ';edit_event_form?uid=%s' % uid
        if timetable:
            url = '%s&timetable=%s' % (url, timetable)
        if resource_name:
            url = '%s/%s' % (resource_name, url)
        ns['url'] = url

        return ns


    def get_grid_ns_event(self, day, event, resource_name=None,
                          conflicts_list=[], timetable=None):
        """
        Specify the namespace given on views to represent an event.

        day: date selected XXX not used for now
        event: event selected
        resource_name: specify the resource for browse_calendar
        conflicts_list: list of conflicts for current resource, [] if not used
        timetable: timetable index

        By default, we get:

          DTSTART: HH:MM, DTEND: HH:MM, TIME: True
            or
          DTSTART: '', DTEND: '', TIME: False
  
          SUMMARY: 'summary of the event'
          STATUS: 'status' (class: cal_conflict, if uid in conflicts_list)
          ORGANIZER: 'organizer of the event'

          url: url to access edit_event_form on current event
        """
        properties = event.get_property_values
        ns = {}
        ns['SUMMARY'] = properties('SUMMARY').value
        ns['ORGANIZER'] = properties('ORGANIZER').value

        ###############################################################
        # Set dtstart and dtend values as time
        ns['start'] = Time.encode(properties('DTSTART').value.time())
        ns['end'] = Time.encode(properties('DTEND').value.time())
        # Add both of these dates into one item
        ns['TIME'] = '%s - %s' % (ns['start'], ns['end']) 

        ###############################################################
        # Set class for conflicting events or just from status value
        uid = event.uid
        if uid in conflicts_list:
            ns['STATUS'] = 'cal_conflict'
        else:
            status = properties('STATUS')
            if status:
                ns['STATUS'] = properties('STATUS').value
            else:
                ns['STATUS'] = ''

        ###############################################################
        # Set url to edit_event_form
        ns['UID'] = '%s' % uid
        url = ';edit_event_form?uid=%s' % uid
        if timetable:
            url = '%s&timetable=%s' % (url, timetable)
        if resource_name:
            url = '%s/%s' % (resource_name, url)
        ns['url'] = url

        return ns


    # Monthly view
    monthly_view__access__ = 'is_allowed_to_view'
    monthly_view__label__ = u'View'
    monthly_view__sublabel__ = u'Monthly'
    def monthly_view(self, context):
        ndays = 7

        # Add ical css
        css = self.get_handler('/ui/ical/calendar.css')
        context.styles.append(str(self.get_pathto(css)))

        # Current date
        c_date = self.get_current_date(context.get_form_value('date', None))
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

        # Get events occurring into current time window
        events = self.search_events_in_range(start, end, sortby='date')

        ###################################################################
        namespace = {}
        # Add header to navigate into time
        namespace = self.add_selector_ns(c_date, 'monthly_view', namespace)
        # Get header line with days of the week
        namespace['days_of_week'] = self.days_of_week_ns(start, ndays=ndays)
        ###################################################################

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
                    ns_day['selected'] = (day == c_date)
                    ns_day['url'] = ';edit_event_form?date=%s' % Date.encode(day)
                    #######################################################
                    # For each day, we add events occuring on this day
                    # We keep events until they end.
                    ns_events = []
                    if events != []:
                        index = 0
                        while index < len(events):
                            event = events[index]
                            e_dtstart = event.get_property_values('DTSTART')
                            e_dtstart = e_dtstart.value.date()
                            e_dtend = event.get_property_values('DTEND')
                            e_dtend = e_dtend.value.date()
                            # Current event occurs on current date
                            # event begins during current tt
                            starts_on = e_dtstart == day
                            # event ends during current tt
                            ends_on = e_dtend == day
                            # event begins before and ends after
                            out_on = (e_dtstart < day and e_dtend > day)

                            if starts_on or ends_on or out_on:
                                ns_event = self.get_ns_event(day, event,
                                                starts_on=starts_on, 
                                                ends_on=ends_on, out_on=out_on)
                                ns_events.append(ns_event)
                                # Current event end on current date
                                if e_dtend == day:
                                    events.remove(event)
                                    if events == []:
                                        break
                                else:
                                    index = index + 1
                            # Current event occurs only later
                            elif e_dtstart > day:
                                break
                            else:
                                index = index + 1
                    #######################################################

                    ns_day['events'] = ns_events
                    ns_week['days'].append(ns_day)
                    if day.day == 1:
                        month = self.gettext(self.months[day.month])
                        ns_week['month'] = month
                day = day + timedelta(1)
            namespace['weeks'].append(ns_week)

        add_icon = self.get_handler('/ui/images/button_add.png')
        namespace['add_icon'] = self.get_pathto(add_icon)

        handler = self.get_handler('/ui/ical/ical_monthly_view.xml')
        return stl(handler, namespace)


    # Weekly view
    weekly_view__access__ = 'is_allowed_to_view'
    weekly_view__label__ = u'View'
    weekly_view__sublabel__ = u'Weekly'
    def weekly_view(self, context):
        ndays = 7

        # Add ical css
        css = self.get_handler('/ui/ical/calendar.css')
        context.styles.append(str(self.get_pathto(css)))

        # Current date
        c_date = context.get_form_value('date', None)
        if not c_date:
            c_date = context.get_cookie('selected_date')
        c_date = self.get_current_date(c_date)
        # Save selected date
        context.set_cookie('selected_date', c_date)

        # Method
        method = context.get_cookie('method')
        if method != 'weekly_view':
            context.set_cookie('method', 'weekly_view')

        ###################################################################
        # Calculate start of current week
        # 0 = Monday, ..., 6 = Sunday
        weekday = c_date.weekday()
        start = c_date - timedelta(weekday)
        if self.get_first_day() == 0:
            start = start - timedelta(1)

        ###################################################################
        namespace = {}
        # Add header to navigate into time
        namespace = self.add_selector_ns(c_date, 'weekly_view' ,namespace)

        ###################################################################
        # Get icon to appear to add a new event
        add_icon = self.get_handler('/ui/images/button_add.png')
        namespace['add_icon'] = self.get_pathto(add_icon)

        ###################################################################
        # Get header line with days of the week
        days_of_week_ns = self.days_of_week_ns(start, True, ndays, c_date)
        ns_headers = []
        for day in days_of_week_ns:
            ns_header = '%s %s' % (day['name'], day['nday'])
            # XXX Use 'selected' for css class to highlight selected date
            ns_headers.append(ns_header)

        ###################################################################
        # Calculate timetables and events occurring for current week
        timetables = self.get_timetables_grid_ns(start)
        events = self.get_grid_events(start, headers=ns_headers)
        ###################################################################
        # Fill data with grid (timetables) and data (events for each day)
        timetable = gridlayout.get_data(events, timetables, start)
        namespace['timetable_data'] = timetable

        handler = self.get_handler('/ui/ical/ical_grid_weekly_view.xml')
        return stl(handler, namespace)


    edit_event_form__access__ = 'is_allowed_to_edit'
    edit_event_form__label__ = u'Edit'
    edit_event_form__sublabel__ = u'Event'
    def edit_event_form(self, context):
        # Add ical css
        css = self.get_handler('/ui/ical/calendar.css')
        context.styles.append(str(self.get_pathto(css)))

        uid = context.get_form_value('uid', None)
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
                c_date = self.get_current_date(selected_date)
                selected_date = Date.encode(c_date)

        # Timetables
        timetable = context.get_form_value('timetable', None)
        tt_start = context.get_form_value('start', None)
        tt_end = None
        if timetable:
            timetables = self.get_timetables()
            if timetables != []:
                timetable = timetables[int(timetable)]
                tt_start = timetable['start']
                tt_end = timetable['end']
        else:
            tt_start = context.get_form_value('start_time', tt_start)
            tt_end = context.get_form_value('end_time', None)
            if tt_start:
                tt_start = Time.decode(tt_start)
            if tt_end:
                tt_end = Time.decode(tt_end)

        # Initialization
        namespace = {}
        namespace['remove'] = None
        event = None
        properties = []
        status = Status()

        # Existant event
        if uid:
            namespace['UID'] = uid
            event = self.get_component_by_uid(uid)
            if not event:
                message = u'Event not found'
                return context.come_back(message, goto=goto)
            namespace['remove'] = True
            properties = event.get_property_values()
            # Get values
            for key in properties:
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
        namespace['allowed'] = self.is_organizer_or_admin(context, event)
        # Set first day of week
        namespace['firstday'] = self.get_first_day()

        handler = self.get_handler('/ui/ical/ical_edit_event_form.xml')
        return stl(handler, namespace)


    edit_event__access__ = 'is_allowed_to_edit'
    def edit_event(self, context):
        if context.has_form_value('remove'):
            return self.remove(context)

        # Method
        method = context.get_cookie('method') or 'monthly_view'
        goto = ';%s' % method
        if method not in dir(self):
            goto = '../;%s' % method

        # Keys to exclude from url
        keys = context.get_form_keys()

        # Get selected_date from the 3 fields 'dd','mm','yyyy' into 'yyyy/mm/dd'
        v_items = []
        for item in ('year', 'month', 'day'):
            v_items.append(context.get_form_value('DTSTART_%s' % item))
        selected_date = '-'.join(v_items)

        # Cancel
        if context.has_form_value('cancel'):
            return context.come_back('', goto, exclude=keys)

        # Get UID and Component object
        properties = {}
        uid = context.get_form_value('uid')
        if uid:
            event = self.get_component_by_uid(uid)
            # Test if current user is admin or organizer of this event
            if not self.is_organizer_or_admin(context, event):
                message = u'You are not authorized to modify this event.'
                return context.come_back(goto, message, exclude=keys)
        else:
            # Add user as Organizer
            organizer = context.user.get_abspath()
            properties['ORGANIZER'] = PropertyValue(organizer)

        for key in context.get_form_keys():
            if key == 'uid':
                continue
            elif key == 'update':
                continue
            # Get date and time for DTSTART and DTEND
            elif key.startswith('DTSTART_day'):
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
                    v_time = '%s:%s' % (hours, minutes)
                    # Append time to date into value
                    params = {}
                    if v_time == ':':
                        value = v_date
                        params['VALUE'] = ['DATE']
                    else:
                        value = ' '.join([v_date, v_time])
                    # Get value as a datetime object
                    try:
                        value = DateTime.from_str(value)
                    except:
                        # Remove event if new one
                        if not uid:
                            uid = event.uid
                            icalendar.remove(self, uid)
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
                    # Remove event if new one
                    if not uid:
                        uid = event.uid
                        icalendar.remove(self, uid)
                    return context.come_back(goto=goto, message=message)
                # Save values
                for key in ('DTSTART', 'DTEND'):
                    value = PropertyValue(values[key][0], **values[key][1])
                    properties[key] = value
            elif key.startswith('DTSTART') or key.startswith('DTEND'):
                continue
            else:
                datatype = self.get_datatype(key)
                values = context.get_form_values(key)

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
        return context.come_back(u'Data updated', goto=goto, exclude=keys)


    remove__access__ = 'is_allowed_to_edit'
    def remove(self, context):
        # Method
        method = context.get_cookie('method') or 'monthly_view'
        goto = ';%s?%s' % (method, self.get_current_date())
        if method not in dir(self):
            goto = '../;%s?%s' % (method, self.get_current_date())

        uid = context.get_form_value('uid') 
        if not uid:
            return context.come_back('', goto)
        icalendar.remove(self, uid)
        return context.come_back(u'Event definitely deleted.', goto=goto)


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
        if self.get_property('timetables'):
            timetables = self.get_timetables()
            for index, timetable in enumerate(timetables):
                ns = {}
                ns['index'] = index
                ns['startname'] = '%s_start' % index
                ns['endname'] = '%s_end' % index
                ns['start'] = Time.encode(timetable['start'])
                ns['end'] = Time.encode(timetable['end'])
                namespace['timetables'].append(ns)
        handler = self.get_handler('/ui/ical/ical_edit_timetables.xml')
        return stl(handler, namespace)


    edit_timetables__access__ = True
    def edit_timetables(self, context):
        timetables = []
        if self.get_property('timetables'):
            timetables = self.get_timetables()

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
            timetables = new_timetables
            message = u'Timetable(s) removed successfully.'

        else:
            # Update timetable or just set index to next index
            for index, timetable in enumerate(timetables):
                for key in ('start', 'end'):
                    value = context.get_form_value('%s_%s' % (index, key), None)
                    if not value or value == '__:__':
                        return context.come_back(u'Wrong time selection.')
                    try:
                        timetable[key] = Time.decode(value)
                    except:
                        message = u'Wrong time selection (HH:MM).'
                        return context.come_back(message=message)
                if timetable['start'] >= timetable['end']:
                    message = u'Start time must be earlier than end time.'
                    return context.come_back(message=message)

            # Add a new timetable
            if context.has_form_value('add'):
                timetable = {}
                for key in ('start', 'end'):
                    value = context.get_form_value('new_%s' % key, None)
                    if not value or value == '__:__':
                        return context.come_back(u'Wrong time selection.')
                    try:
                        timetable[key] = Time.decode(value)
                    except:
                        message = u'Wrong time selection (HH:MM).'
                        return context.come_back(message=message)
                if timetable['start'] >= timetable['end']:
                    message = u'Start time must be earlier than end time.'
                    return context.come_back(message=message)
                timetables.append(timetable)
                timetables.sort(lambda x, y: cmp(x['start'], y['start']))

            message = u'Timetables updated successfully.'

        # Save new value into metadata
        str_timetables = []
        for timetable in timetables:
            start = timetable['start']
            end = timetable['end']
            start = '(' + str(start.hour) + ',' + str(start.minute) + ')'
            end = '(' + str(end.hour) + ',' + str(end.minute) + ')'
            str_timetable = start + ',' + end
            str_timetables.append(str_timetable)
        str_timetables = ';'.join(str_timetables)
        self.set_property('timetables', str_timetables)

        return context.come_back(message=message)
        

register_object_class(Calendar)



class CalendarAware(object):

    # Start 07:00, End 21:00, Interval 30min
    class_cal_range = (time(7,0), time(21,0), 30)
    class_cal_fields = ('SUMMARY', 'DTSTART', 'DTEND')
    class_weekly_shown = ('SUMMARY', )


    def get_cal_range(cls):
        return cls.class_cal_range


    def get_cal_fields(cls):
        return cls.class_cal_fields


    def get_weekly_shown(cls):
        return cls.class_weekly_shown


    @classmethod
    def get_default_timetables(cls, interval, start_time, end_time):
        # Default datetime values
        start =  datetime(2000, 1, 1)
        end =  datetime(2000, 1, 1, 23, 59)
        # Set given start_time
        if start_time:
            start = datetime.combine(start.date(), start_time)
        # Set given end_time
        if end_time:
            end = datetime.combine(start.date(), end_time)
        # Get timetables for a given interval in minutes, by default 1 day 
        timetables, tt_start = [], start
        while tt_start < end:
            tt_end = tt_start + timedelta(minutes=interval)
            timetable = {'index': None,
                         'start': tt_start.time(),
                         'end': tt_end.time()}
            timetables.append(timetable)
            tt_start = tt_end
        return timetables


    # Get one line with times of timetables
    def get_header_timetables(self, timetables, delta=45):
        current_date = date.today()
        timetable = timetables[0]
        last_start = timetable['start']
        last_start = datetime.combine(current_date, last_start)

        ns_timetables = []
        # Add first timetable start time
        ns_timetable =  {'start': last_start.strftime('%H:%M')}
        ns_timetables.append(ns_timetable)

        # Add next ones if delta time > delta minutes
        for timetable in timetables[1:]:
            tt_start = timetable['start']
            tt_start = datetime.combine(current_date, tt_start)
            if tt_start - last_start > timedelta(minutes=delta):
                ns_timetable =  {'start': tt_start.strftime('%H:%M')}
                ns_timetables.append(ns_timetable)
                last_start = tt_start
            else:
                ns_timetables.append({'start': None})

        return ns_timetables


    # Get one line with header and empty cases with only '+'
    def get_header_columns(self, calendar_url, args, timetables, cal_fields, 
                           new_class='add_event', new_value='+'):
        ns_columns = []
        for timetable in timetables:
            start = Time.encode(timetable['start'])
            end = Time.encode(timetable['end'])

            tmp_args = args + '&start_time=%s' % start
            tmp_args = tmp_args + '&end_time=%s' % end
            new_url = '%s/;edit_event_form?%s' % (calendar_url, tmp_args)

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


    def get_ns_calendar(self, calendar, c_date, cal_fields, shown_fields, 
                        timetables, method='browse_calendar', 
                        show_conflicts=False):
        calendar_url = self.get_pathto(calendar)
        args = 'date=%s&method=%s' % (Date.encode(c_date), method)
        new_url = '%s/;edit_event_form?%s' % (calendar_url, args)

        ns_calendar = {}
        ns_calendar['name'] = calendar.get_title_or_name()

        ###############################################################
        # Get a dict for each event with shown_fields, tt_start, tt_end, 
        # uid and colspan ; the result is a list sorted by tt_start
        ns_events = calendar.get_ns_events(c_date, shown_fields, timetables)

        # Get conflicts in events if activated
        if show_conflicts:
            conflicts = calendar.get_conflicts(c_date)
            conflicts_list = set()
            if conflicts:
                [conflicts_list.update(uids) for uids in conflicts]

        ###############################################################
        # Organize events in rows
        rows = []
        for index, tt in enumerate(timetables):
            row_index = 0 
            # Search events in current timetable
            for index_event, event in enumerate(ns_events):
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
        ###############################################################
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
            for tt_index, timetable in enumerate(timetables):
                if colspan > 0:
                    colspan = colspan - 1
                    continue
                start = Time.encode(timetable['start'])
                end = Time.encode(timetable['end'])
                tmp_args = args + '&start_time=' + start
                tmp_args = tmp_args + '&end_time=' + end
                new_url = '%s/;edit_event_form?%s' % (calendar_url, tmp_args)
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
                    event_params = '%s&uid=%s' % (args, uid)
                    go_url = '%s/;edit_event_form?%s' % (calendar_url,
                                                         event_params) 
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

        ###############################################################
        # Add ns_rows to namespace
        ns_calendar['rows'] = ns_rows

        ###############################################################
        # Add one line with header and empty cases with only '+'
        header_columns = self.get_header_columns(calendar_url, args, 
                                                 timetables, cal_fields)
        ns_calendar['header_columns'] = header_columns 

        ###############################################################
        # Add url to calendar keeping args
        ns_calendar['url'] = '%s/;monthly_view?%s' % (calendar_url, args)
        ns_calendar['rowspan'] = len(rows) + 1

        return ns_calendar


    browse_calendar__access__ = 'is_allowed_to_edit'
    browse_calendar__label__ = u'Contents'
    browse_calendar__sublabel__ = u'As calendar'
    def browse_calendar(self, context):
        # Add ical css
        css = self.get_handler('/ui/ical/calendar.css')
        context.styles.append(str(self.get_pathto(css)))

        # Set calendar as selected browse view
        context.set_cookie('browse', 'calendar')

        # Current date
        selected_date = context.get_form_value('date', None)
        c_date = Calendar.get_current_date(date)
        if not selected_date:
            selected_date = Date.encode(c_date)

        # Start and end times, and interval
        c_start_time, c_end_time, interval = self.get_cal_range()
        start_time = datetime.combine(c_date, c_start_time)
        end_time = datetime.combine(c_date, c_end_time)

        # Get fields and fields to show
        cal_fields = self.get_cal_fields()
        shown_fields = self.get_weekly_shown()

        namespace = {}
        # Add date selector
        namespace['date'] = selected_date
        namespace['firstday'] = Calendar.get_first_day()
        namespace['link_on_summary'] = True

        # Get default timetables
        timetables = self.get_default_timetables(interval=interval,
                      start_time=c_start_time, end_time=c_end_time)

        ###############################################################
        # Add a header line with start time of each timetable
        namespace['header_timetables'] = self.get_header_timetables(timetables)
        
        ###################################################################
        # For each found calendar
        calendars = self.search_handlers(handler_class=Calendar)
        ns_calendars = []
        for calendar in calendars:
            ns_calendar = self.get_ns_calendar(calendar, c_date, cal_fields, 
                                               shown_fields, timetables)
            ns_calendars.append(ns_calendar)
        namespace['calendars'] = ns_calendars

        handler = self.get_handler('/ui/ical/Folder_browse_calendar.xml')
        return stl(handler, namespace)

