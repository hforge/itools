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
from datetime import datetime, time, timedelta

# Import from itools
from itools import i18n
from itools.datatypes import Unicode
from itools.ical.icalendar import icalendar, Component, PropertyValue
from itools.ical.icalendar import Parameter
from itools.ical.types import data_properties, DateTime
from itools.stl import stl
from itools.web import get_context
from File import File
from registry import register_object_class

# Import from itools.cms
from itools.cms.text import Text
from itools.cms.Handler import Handler
from itools.cms.metadata import Enumerate


class Status(Enumerate):

    options = [{'name': 'TENTATIVE', 'value': u'TENTATIVE'},
               {'name': 'CONFIRMED', 'value': u'CONFIRMED'}, 
               {'name': 'CANCELLED', 'value': u'CANCELLED'}]



class Calendar(Text, icalendar):

    class_id = 'calendar'
    class_version = '20060720'
    class_title = u'Calendar'
    class_description = u'Schedule your time with calendar files.'
    class_icon16 = 'images/icalendar16.png'
    class_icon48 = 'images/icalendar48.png'
    class_views = [['monthly_view', 'weekly_view', 'text_view', 
                    'download_form'], 
                   ['upload_form', 'edit_timetables_form',
                    'edit_metadata_form']]
    #               ['history_form']]
    # default values for fields within namespace
    default_fields = {'UID': None, 'DTSTART1': None, 'DTEND1': None, 
                      'SUMMARY': u'', 'LOCATION': u'', 'DESCRIPTION': u'', 
                      'ATTENDEE': [], 'COMMENT': [], 
                      'STATUS': {}}
    # default viewed fields on monthly_view
    default_viewed_fields = ('DTSTART', 'DTEND', 'SUMMARY', 'STATUS')
    months = {1: u'January', 2: u'February', 3: u'March', 4: u'April', 
              5: u'May', 6: u'June', 7: u'July', 8: u'August', 9: u'September',
              10: u'October', 11: u'November', 12: u'December'}
    days = {0: u'Monday', 1: u'Tuesday', 2: u'Wednesday', 3: u'Thursday', 
            4: u'Friday', 5: u'Saturday', 6: u'Sunday'}


    edit_metadata_form__sublabel__ = u'Metadata'


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
    def get_current_date(cls, date=None):
        # Set current date to selected date (default is today)
        if not date:
            # Today in format AAAA-MM-DD
            today = datetime.today()
            date = today.strftime('%Y-%m-%d')
        try:
            year, month, day = date.split('-')
            year, month, day = int(year), int(month), int(day)
            return datetime(year, month, day)
        except:
            return cls.get_current_date()


    # Get namespace for one selected day, filling given fields
    def get_events(self, date, method='monthly_view', timetable=None, 
                   fields=None, resource_name=None):
        # If no date, return []
        if date is None:
            return []
        # If no tuple of fields given, set default one
        if fields == None:
            fields = self.default_viewed_fields
        # Initialize url
        base_url = ';edit_event_form?'
        if resource_name:
            base_url = '%s/;edit_event_form?' % resource_name

        # Get events on selected date
        if timetable:
            index = timetable['num']
            start = datetime.combine(date, timetable['start'])
            end = datetime.combine(date, timetable['end'])
            events = self.get_events_in_range(start, end)
            base_url = '%stimetable=%s&' % (base_url, index)
        else:
            events = self.get_events_in_date(date)

        # For each event, fill namespace
        namespace = []
        for event in events:
            uid = event.get_property_values('UID').value
            ns_event = {'DTSTART': None, 'DTEND': None, 'TIME': None, 
                        'STATUS': 'TENTATIVE'}

            # - Show start-end times only if event starts and ends on the
            # same day and has no parameter VALUE=DATE, as a string HH:MM
            # - Show only "start time...", "..." and "...end time" if xx days
            if 'DTSTART' in fields:
                value = event.get_property_values('DTSTART')
                value, params = value.value, value.parameters
                param = params.get('VALUE', '')
                if not param or param.values != ['DATE']:
                    # Get DTEND value
                    if 'DTEND' not in fields:
                        value2 = value
                    else:
                        value2 = event.get_property_values('DTEND').value
                    v_date, v2_date = value.date(), value2.date()
                    # Get printable times
                    ns_start = value.strftime('%H:%M')
                    ns_end = value2.strftime('%H:%M')
                    # Only one day
                    if v_date == v2_date:
                        ns_event['DTSTART'] = ns_start
                        ns_event['DTEND'] = ns_end
                        ns_event['TIME'] = True
                    # On first day
                    elif v_date == date.date():
                        ns_event['DTSTART'] = '%s...' % ns_start
                        ns_event['TIME'] = True
                    # On last day
                    elif v2_date == date.date():
                        ns_event['DTEND'] = '...%s' % ns_end
                        ns_event['TIME'] = True
                    # Neither first nor last day
                    else:
                        ns_event['DTSTART'] = '...'
                        ns_event['TIME'] = True

            # Manage other fields
            for field in fields:
                if field not in ('DTSTART', 'DTEND'):
                    values = event.get_property_values(field)
                    ns_event[field] = self.ns_values(values)

            ns_event['url'] = '%sdate=%s&uid=%s&method=%s'\
                              % (base_url, date.date(), uid, method)
            namespace.append(ns_event)

        return namespace


    def ns_values(self, values):
        if not isinstance(values, list):
            return values.value
        for value in values:
            value = values.value
        return values


    @classmethod
    def add_selector_ns(cls, c_date, method, namespace):
        # Set header used to navigate into time
        # Week, current date is first showed week + 1
        tmp_date = c_date - timedelta(7)
        current_week = cls.gettext(u'Week ')
        current_week = current_week + Unicode.encode(tmp_date.strftime('%U'))
        previous_week = ";%s?date=%s" % (method, tmp_date.date())
        tmp_date = c_date + timedelta(7)
        next_week = ";%s?date=%s" % (method, tmp_date.date())
        # Month
        current_month = cls.gettext(cls.months[c_date.month])
        tmp_date = c_date - timedelta(30)
        previous_month = ";%s?date=%s" % (method, tmp_date.date())
        tmp_date = c_date + timedelta(30)
        next_month = ";%s?date=%s" % (method, tmp_date.date())
        # Year
        tmp_date = c_date - timedelta(365)
        previous_year = ";%s?date=%s" % (method, tmp_date.date())
        tmp_date = c_date + timedelta(365)
        next_year = ";%s?date=%s" % (method, tmp_date.date())
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
        return namespace


    # Test if user in context is the organizer of a given event (or is admin)
    def is_organizer_or_admin(self, context, event):
        if self.get_access_control().is_admin(context.user):
            return True
        if event:
            organizer = event.get_property_values('ORGANIZER')
            if organizer:
                return context.user.uri == organizer.value
        return False
          

    # 0 means Sunday, 1 means Monday
    @classmethod
    def get_first_day(cls):
        return 1


    # Get days of week based on get_first_day's result 
    @classmethod
    def days_of_week_ns(cls, date, num=None, ndays=7):
        ns_days = []
        for index in range(ndays):
            ns =  {}
            ns['name'] = cls.gettext(cls.days[date.weekday()])
            ns['nday'] = None
            if num:
                ns['nday'] = date.day
            ns_days.append(ns)
            date = date + timedelta(1)
        return ns_days


    # Get the list of all timetables with label, start and end in a dict
    def get_timetables(self, default=None):
        timetables = []
        for index in range(10):
            src_timetable = self.get_property('timetable_%s' % index)
            if not src_timetable:
                break
            timetables.append(self.get_timetable_from_string(index, 
                                                             src_timetable))
        # If timetable required and none found, add default one
        if timetables == [] and default:
            timetable = {'num': 0,
                         'timetable': u'',
                         'start': time(0,0),
                         'end': time(23,59,59)}
            timetables.append(timetable)
        # Sort by start time
        timetables.sort(lambda x, y: cmp(x['start'], y['start']))
        return timetables


    # Get timetable as dict from a string like "08:00 - 10:00" or "08:00-10:00"
    def get_timetable_by_index(self, index):
        timetable = self.get_property('timetable_%s' % index)
        if timetable:
            return self.get_timetable_from_string(index, timetable)
        return None


    # Get timetable as dict from a string like "08:00 - 10:00" or "08:00-10:00"
    def get_timetable_from_string(self, index, timetable):
        start, end = timetable.split('-')
        ns = {}
        ns['num'] = index
        ns['timetable'] = timetable.replace('-', ' - ')
        hour, minute = start.split(':')
        ns['start'] = time(int(hour), int(minute))
        hour, minute = end.split(':')
        ns['end'] = time(int(hour), int(minute))
        return ns
        

    # Get a week beginning at start date as a list to be given to namespace
    def get_timetables_ns(self, start, method='weekly_view', 
                          resource_name=None, ndays=7):
        ns = []
        # Initialize url and parameters
        base_url = ';edit_event_form?'
        if resource_name:
            base_url = '%s/;edit_event_form?' % resource_name
        base_param = ''
        if method:
            base_param = '&method=%s&' % method
        # Get timetables
        timetables = self.get_timetables(default=True)
        # For each defined timetable
        for index, timetable in enumerate(timetables):
            day = start
            ns_timetable = {}
            ns_timetable['timetable'] = timetable['timetable']
            num = timetable['num']
            # ndays days
            ns_days = []
            for d in range(ndays):
                ns_day = {}
                params = '%sdate=%s&timetable=%s'\
                         % (base_param, day.date(), num)
                ns_day['url'] = '%s%s' % (base_url, params)
                ns_day['events'] = self.get_events(day, method, 
                                                   timetable, 
                                                   resource_name=resource_name)
                ns_days.append(ns_day)
                day = day + timedelta(1)
            ns_timetable['days'] = ns_days
            ns.append(ns_timetable)
        return ns

    #######################################################################
    # User interface
    #######################################################################

    download_form__access__ = True #'is_allowed_to_view'
    download_form__sublabel__ = u'Export in ical format'


    # View
    text_view__access__ = True #'is_allowed_to_view'
    text_view__label__ = u'Text view'
    text_view__sublabel__ = u'Text view'
    def text_view(self, context):
        return '<pre>%s</pre>' % self.to_str()


    # Monthly view
    monthly_view__access__ = True #'is_allowed_to_view'
    monthly_view__label__ = u'View'
    monthly_view__sublabel__ = u'Monthly'
    def monthly_view(self, context):
        context = get_context()
        root = context.root

        # Current date
        c_date = self.get_current_date(context.get_form_value('date', None))

        # Calculate start of previous week
        # 0 = Monday, ..., 6 = Sunday
        weekday = c_date.weekday()
        start = c_date - timedelta(7 + weekday)
        if self.get_first_day() == 0:
            start = start - timedelta(1)

        namespace = {}
        # Add header to navigate into time
        namespace = self.add_selector_ns(c_date, 'monthly_view', namespace)

        # Get header line with days of the week
        namespace['days_of_week'] = self.days_of_week_ns(start)

        namespace['weeks'] = []
        day = start
        # 5 weeks
        for w in range(5):
            ns_week = {'days': [], 'month': u''}
            # 7 days
            for d in range(7):
                ns_day = {}
                ns_day['nday'] = day.day
                ns_day['url'] = ';edit_event_form?date=%s' % day.date()
                ns_day['events'] = self.get_events(day, 'monthly_view')
                ns_week['days'].append(ns_day)
                if day.day == 1:
                    month = self.gettext(self.months[day.month])
                    ns_week['month'] = month
                day = day + timedelta(1)
            namespace['weeks'].append(ns_week)

        handler = root.get_handler('ui/ical_monthly_view.xml')
        return stl(handler, namespace)


    # Weekly view
    weekly_view__access__ = True #'is_allowed_to_view'
    weekly_view__label__ = u'View'
    weekly_view__sublabel__ = u'Weekly'
    def weekly_view(self, context):
        context = get_context()
        root = context.root

        # Current date
        c_date = self.get_current_date(context.get_form_value('date', None))

        # Calculate start of current week
        # 0 = Monday, ..., 6 = Sunday
        weekday = c_date.weekday()
        start = c_date - timedelta(weekday)
        if self.get_first_day() == 0:
            start = start - timedelta(1)

        namespace = {}
        # Add header to navigate into time
        namespace = self.add_selector_ns(c_date, 'weekly_view' ,namespace)

        # Get header line with days of the week
        namespace['days_of_week'] = self.days_of_week_ns(start, num=True)

        # Get 1 week with all defined timetables or none (just one line)
        namespace['timetables'] = self.get_timetables_ns(start)

        handler = root.get_handler('ui/ical_weekly_view.xml')
        return stl(handler, namespace)


    edit_event_form__access__ = True #'is_allowed_to_edit'
    edit_event_form__label__ = u'Edit'
    edit_event_form__sublabel__ = u'Event'
    def edit_event_form(self, context):
        context = get_context()
        root = context.root

        uid = context.get_form_value('uid', None)
        method = context.get_form_value('method', 'monthly_view')
        goto = ';%s' % method 

        date = context.get_form_value('date', None)
        if not date:
            message = u'A date must be specified to edit an event'
            return context.come_back(message, goto=goto)
        # date as a datetime object
        c_date = self.get_current_date(date)

        # Timetables
        tt_start, tt_end = None, None
        timetable = context.get_form_value('timetable', None)
        if timetable:
            timetables = self.get_timetables()
            if timetables != []:
                timetable = timetables[int(timetable)]
                tt_start = timetable['start'].strftime('%H:%M')
                tt_end = timetable['end'].strftime('%H:%M')

        # Initialization
        namespace = {}
        event = None
        properties = []
        status = Status()

        # Existant event
        if uid:
            event = self.get_component_by_uid(uid)
            if not event:
                message = u'Event not found'
                goto = '%s?date=%s' % (goto,date)
                return context.come_back(message, goto=goto)
            properties = event.get_property_values()
            # Get values
            for key in properties:
                value = properties[key]
                if isinstance(value, list):
                    namespace[key] = value
                elif key == 'STATUS':
                    namespace['STATUS'] = status.get_namespace(value.value)
                # Split DTSTART field into 2 fields : (1)date and (2)time 
                elif key in ('DTSTART', 'DTEND'):
                    value, params = value.value, value.parameters
                    namespace['%s1'%key] = value.date()
                    param = params.get('VALUE', '')
                    if not param or param.values != ['DATE']:
                        namespace['%s2'%key] = value.time().strftime('%H:%M')
                    else:
                        namespace['%s2'%key] = '__:__'
                else:
                    namespace[key] = value.value


        # Default managed fields are :
        # SUMMARY, LOCATION, DTSTART, DTEND, DESCRIPTION, 
        # STATUS ({}), ATTENDEE ([]), COMMENT ([])
        fields = self.default_fields
        fields['STATUS'] = status.get_namespace('TENTATIVE')
        for field in self.default_fields:
            if field not in namespace:
                namespace[field] = self.default_fields[field]
                if field == 'DTSTART1':
                    namespace['DTSTART1'] = date
                    namespace['DTSTART2'] = tt_start or '__:__'
                elif field == 'DTEND1':
                    namespace['DTEND1'] = date
                    namespace['DTEND2'] = tt_end or '__:__'

        # Get attendees -- add blank one if no attendee at all
#        if namespace['ATTENDEE'] == []:
#            namespace['ATTENDEE'] = self.attendees_namespace()
#        else:
#            attendees_list.append(PropertyValue(''))
#            attendees = self.attendees_namespace(attendees_list)

#        # Get attendees -- add blank one if no attendee at all
#        if not attendees_list:
#            attendees = self.attendees_namespace()
#        else:
#            attendees_list.append(PropertyValue(''))
#            attendees = self.attendees_namespace(attendees_list)
#
#        # Get comments -- add blank one if no comment at all
#        if not comments_list:
#            comments_list = []
#        # Add a blank comment for a new one
#        comments_list.append(PropertyValue(''))
#        comments = []
#        for i, comment in enumerate(comments_list):
#            # Allow only one empty value at last position
#            if comment.value != '' or i == (len(comments_list)-1):
#                ns_comment = {}
#                ns_comment['name'] = 'COMMENT.%s' % i
#                ns_comment['value'] = comment.value
#                comments.append(ns_comment)

        # Call to gettext on Status values
        for status in namespace['STATUS']:
            status['value'] = self.gettext(status['value'])
        # Show action buttons only if current user is authorized
        namespace['allowed'] = self.is_organizer_or_admin(context, event)
        # Set first day of week
        namespace['firstday'] = self.get_first_day()
        # Keep params
        namespace['method'] = method

        handler = root.get_handler('ui/ical_edit_event_form.xml')
        return stl(handler, namespace)


    edit_event__access__ = True #'is_allowed_to_edit'
    def edit_event(self, context):
        if context.has_form_value('remove'):
            return self.remove(context)

        method = context.get_form_value('method', 'monthly_view')
        goto = ';%s' % method
        if method not in dir(self):
            goto = '../;%s' % method

        date = self.get_current_date(context.get_form_value('DTSTART1'))
        # Get UID and Component object
        uid = context.get_form_value('UID')
        if uid:
            event = self.get_component_by_uid(uid)
            # Test if current user is admin or organizer of this event
            if not self.is_organizer_or_admin(context, event):
                message = u'You are not authorized to modify this event.'
                return context.come_back(goto, message)
        else:
            event = Component('VEVENT')
            # Add user as Organizer
            organizer = context.user.uri
            organizer = PropertyValue(organizer)
            event.set_property('ORGANIZER', organizer)
            self.add(event)

        for key in context.get_form_keys():
            if key == 'UID':
                continue
            elif key in ('update', 'method'):
                continue
            # Get date and time for DTSTART and DTEND
            elif key[:-1] in ('DTSTART', 'DTEND'):
                real_key, number = key[:-1], key[-1]
                if number == '1':
                    v_date = context.get_form_value(key)
                    v_time = context.get_form_value('%s2' % real_key, '')
                    params = {}
                    if v_time in ('__:__', ''):
                        value = v_date
                        params['VALUE'] = Parameter('VALUE', ['DATE'])
                    else:
                        value = ' '.join([v_date, v_time])
                    try:
                        value = DateTime.from_str(value)
                    except:
                        message = u'One or more field is invalid.'
                        return context.come_back(goto, message)
                    value = PropertyValue(value, params)
                    event.set_property(real_key, value)
            else:
                values = context.get_form_values(key)
                type = data_properties.get(key, Unicode)

                decoded_values = []
                for value in values:
                    value = type.decode(value)
                    decoded_values.append(PropertyValue(value))
                event.set_property(key, decoded_values)
        # Change timestamp
        event.set_property('DTSTAMP', PropertyValue(datetime.today()))

        self.set_changed()
        goto = '%s?date=%s' % (goto, date.strftime('%Y-%m-%d'))
        return context.come_back(u'Data updated', goto=goto)


    remove__access__ = True
    def remove(self, context):
        uid = context.get_form_value('UID') 
        method = context.get_form_value('method', 'monthly_view')
        icalendar.remove(self, 'VEVENT', uid)
        goto = ';%s?%s' % (method, self.get_current_date())
        if method not in dir(self):
            goto = '../;%s?%s' % (method, self.get_current_date())
        return context.come_back(u'Event definitely deleted.', goto=goto)


    edit_timetables_form__access__ = True
    edit_timetables_form__label__ = u'Edit'
    edit_timetables_form__sublabel__ = u'Timetables'
    def edit_timetables_form(self, context):
        context = get_context()
        root = context.root
        # Initialization
        namespace = {}
        timetables = self.get_timetables()
        namespace['timetables'] = []
        for index, timetable in enumerate(timetables):
            num = timetable['num']
            ns = {}
            ns['index'] = num
            ns['startname'] = '%s_startname' % num
            ns['endname'] = '%s_endname' % num
            ns['start'] = timetable['start'].strftime('%H:%M')
            ns['end'] = timetable['end'].strftime('%H:%M')
            namespace['timetables'].append(ns)
        handler = root.get_handler('ui/ical_edit_timetables.xml')
        return stl(handler, namespace)


    edit_timetables__access__ = True
    def edit_timetables(self, context):
        ##############################################################
        # Remove selected lines
        if context.has_form_value('remove'):
            ids = context.get_form_values('ids')
            for index in range(10):
                if str(index) in ids:
                    # Delete selected timetable
                    self.del_property('timetable_%s' % index)
                    # Move last timetable to where the deleted one was
                    indexes = range(index, 10)
                    indexes.reverse()
                    for index_2 in indexes:
                        if str(index_2) in ids:
                            continue
                        value = self.get_property('timetable_%s' %index_2)
                        if value:
                            self.set_property('timetable_%s' % index, value)
                            self.del_property('timetable_%s' % index_2)
                            break
                    ids.remove(str(index))
            return context.come_back(u'Timetable removed successfully.')

        ##############################################################
        # Update timetable or just set index to next index
        for index in range(10):
            if not context.has_form_value('%s_startname' %index):
                break
            # Update existing timetable at current index
            if context.has_form_value('update'):
                timetable = {}
                start = context.get_form_value('%s_startname' %index, None)
                end = context.get_form_value('%s_endname' %index, None)
                if not start or not end:
                    return context.come_back(u'Please fill date AND end times.')
                timetable = '%s-%s' % (start, end)
                self.set_property('timetable_%s' % index, timetable)

        ##############################################################
        # Add a new timetable
        if context.has_form_value('add'):
            timetable = {}
            start = context.get_form_value('new_start', None)
            end = context.get_form_value('new_end', None)
            if not start or not end or start == '__:__' or end == '__:__':
                return context.come_back(u'Please fill date AND end times.')
            timetable = '%s-%s' % (start, end)
            self.set_property('timetable_%s' % index, timetable)
        return context.come_back(u'Timetable updated successfully.')
        

register_object_class(Calendar)
