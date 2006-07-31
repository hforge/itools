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
from itools.cms.metadata import Enumerate


class Status(Enumerate):

    options = [{'name': 'TENTATIVE', 'value': 'TENTATIVE'},
               {'name': 'CONFIRMED', 'value': 'CONFIRMED'}, 
               {'name': 'CANCELLED', 'value': 'CANCELLED'}]



class Calendar(Text, icalendar):

    class_id = 'calendar'
    class_version = '20060720'
    class_title = u'Calendar'
    class_description = u'Schedule your time with calendar files.'
    class_icon16 = 'images/icalendar16.png'
    class_icon48 = 'images/icalendar48.png'
    class_views = [['table_view', 'text_view', 'download'], 
                   ['upload_form', 'edit_event_form']]
    #               ,['edit_form', 'externaledit', 'upload_form'],
    #               ['edit_metadata_form'],
    #               ['history_form']]
    # default values for fields within namespace
    default_fields = {'UID': None, 'DTSTART1': None, 'DTEND1': None, 
                      'SUMMARY': u'', 'LOCATION': u'', 'DESCRIPTION': u'', 
                      'ATTENDEE': [], 'COMMENT': [], 
                      'STATUS': {}}
    # default viewed fields on table_view
    default_viewed_fields = ('DTSTART', 'DTEND', 'SUMMARY', 'STATUS')
    # default start and end of the day for current resource/calendar
    default_daystart = time(8,0)
    default_dayend = time(20,0)


    def GET(self, context):
        return self.view(context)


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
    def get_events(self, date, fields=None):
        # If no date, return []
        if date is None:
            return []
        # If no tuple of fields given, set default one
        if fields == None:
            fields = self.default_viewed_fields

        # Get events on selected date
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

            ns_event['url'] = ';edit_event_form?date=%s&uid=%s'\
                              % (date.date(), uid)
            namespace.append(ns_event)

        return namespace


    def ns_values(self, values):
        if not isinstance(values, list):
            return values.value
        for value in values:
            value = values.value
        return values


    def is_allowed_to_edit(self, context, event):
        if self.get_access_control().is_admin(context.user):
            return True
        if event:
            organizer = event.get_property_values('ORGANIZER')
            if organizer:
                return context.user.uri == organizer.value
        return False
          

    def get_first_day(self):
    # 0 means Sunday, 1 means Monday
        return 1

    #######################################################################
    # User interface
    #######################################################################

    download__access__ = True #'is_allowed_to_view'
    download__sublabel__ = u'Export in ical format'

    # View
    text_view__access__ = True #'is_allowed_to_view'
    text_view__label__ = u'Text view'
    text_view__sublabel__ = u'Text view'
    def text_view(self, context):
        return '<pre>%s</pre>' % self.to_str()


    # Table view
    table_view__access__ = True #'is_allowed_to_table_view'
    table_view__label__ = u'View'
    table_view__sublabel__ = u'Table view'
    def table_view(self, context):
        context = get_context()
        root = context.root

        # Current date
        c_date = self.get_current_date(context.get_form_value('date', None))

        # Calculate start of previous week
        # 0 = Monday, ..., 6 = Sunday
        weekday = c_date.weekday()
        start = c_date - timedelta(7 + weekday)

        namespace = {}
        #################################################
        # Set header used to navigate into time
        # Week, current date is first showed week + 1
        tmp_date = c_date - timedelta(7)
        current_week = Unicode.encode('Week %s' % tmp_date.strftime('%U'))
        previous_week = ";table_view?date=%s" % tmp_date.date()
        tmp_date = c_date + timedelta(7)
        next_week = ";table_view?date=%s" % tmp_date.date()
        # Month
        current_month = Unicode.encode(c_date.strftime('%B'))
        tmp_date = c_date - timedelta(30)
        previous_month = ";table_view?date=%s" % tmp_date.date()
        tmp_date = c_date + timedelta(30)
        next_month = ";table_view?date=%s" % tmp_date.date()
        # Year
        tmp_date = c_date - timedelta(365)
        previous_year = ";table_view?date=%s" % tmp_date.date()
        tmp_date = c_date + timedelta(365)
        next_year = ";table_view?date=%s" % tmp_date.date()

        namespace['current_week'] = current_week
        namespace['previous_week'] = previous_week
        namespace['next_week'] = next_week
        namespace['current_month'] = current_month
        namespace['previous_month'] = previous_month
        namespace['next_month'] = next_month
        namespace['current_year'] = c_date.year
        namespace['previous_year'] = previous_year
        namespace['next_year'] = next_year
        #################################################

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
                ns_day['events'] = self.get_events(day)
                ns_week['days'].append(ns_day)
                if day.day == 1:
                    month = self.gettext(Unicode.encode(day.strftime('%B')))
                    ns_week['month'] = month
                day = day + timedelta(1)
            namespace['weeks'].append(ns_week)

        handler = root.get_handler('ui/ical_table_view.xml')
        return stl(handler, namespace)


    edit_event_form__access__ = True #'is_allowed_to_edit'
    edit_event_form__label__ = u'Edit'
    edit_event_form__sublabel__ = u'Edit event'
    def edit_event_form(self, context):
        context = get_context()
        root = context.root
        goto = ';table_view'

        uid = context.get_form_value('uid', None)
        date = context.get_form_value('date', None)
        if not date:
            message = u'A date must be specified to edit an event'
            return context.come_back(message, goto=goto)
        # date as a datetime object
        c_date = self.get_current_date(date)

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
                    namespace['DTSTART2'] = '__:__'
                elif field == 'DTEND1':
                    namespace['DTEND1'] = date
                    namespace['DTEND2'] = '__:__'

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

        # Show action buttons only if current user is the organizer of the event
        # or admin
        namespace['allowed'] = self.is_allowed_to_edit(context, event)
        # Set first day of week
        namespace['firstday'] = self.get_first_day()

        handler = root.get_handler('ui/ical_edit_event_form.xml')
        return stl(handler, namespace)


    edit_event__access__ = True #'is_allowed_to_edit'
    def edit_event(self, context):
        if context.has_form_value('remove'):
            return self.remove(context)

        date = self.get_current_date()
        # Get UID and Component object
        uid = context.get_form_value('UID')
        if uid:
            event = self.get_component_by_uid(uid)
            # Test if current user is admin or organizer of this event
            if not self.is_allowed_to_edit(context, event):
                message = u'You are not authorized to modify this event.'
                return context.come_back(message)
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
            elif key == 'update':
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
                        return context.come_back(message)
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
        goto = ';table_view?date=%s' % date
        return context.come_back(u'Data updated', goto=goto)


    remove__access__ = True
    def remove(self, context):
        uid = context.get_form_value('UID') 
        icalendar.remove(self, 'VEVENT', uid)
        goto = ';table_view?%s' % self.get_current_date()
        return context.come_back(u'Event definitely deleted.', goto=goto)

register_object_class(Calendar)
