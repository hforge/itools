# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Nicolas Deram <nicolas@itaapy.com>
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

# Import from the Standard Library
import unittest
from cStringIO import StringIO
from datetime import datetime

# Import from itools
from itools.csv import Property
from itools.datatypes import URI
from itools.ical import iCalendar, icalendarTable


# Example with 1 event
content = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN
METHOD:PUBLISH
BEGIN:VEVENT
UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a
SUMMARY:Résumé
DESCRIPTION:all all all
LOCATION:France
STATUS:TENTATIVE
CLASS:PRIVATE
X-MOZILLA-RECUR-DEFAULT-INTERVAL:0
DTSTART;VALUE="DATE":20050530
DTEND;VALUE=DATE:20050531
DTSTAMP:20050601T074604Z
ATTENDEE;RSVP=TRUE;MEMBER="mailto:DEV-GROUP@host2.com":mailto:jdoe@itaapy.com
ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com":mailto:jsmith@itaapy.com
PRIORITY:1
SEQUENCE:0
END:VEVENT
END:VCALENDAR
"""

# Example with 2 events
content2 = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN
METHOD:PUBLISH
BEGIN:VEVENT
UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a
SUMMARY:Refound
DESCRIPTION:all all all
LOCATION:France
STATUS:TENTATIVE
CLASS:PRIVATE
X-MOZILLA-RECUR-DEFAULT-INTERVAL:0
DTSTART;VALUE="DATE":20050530T000000
DTEND;VALUE=DATE:20050531T235959.999999
DTSTAMP:20050601T074604Z
ATTENDEE;RSVP=TRUE;MEMBER="mailto:DEV-GROUP@host2.com":mailto:jdoe@itaapy.com
PRIORITY:1
SEQUENCE:0
END:VEVENT
BEGIN:VEVENT
UID:581361a0-1dd2-11b2-9a42-bd3958eeac9b
SUMMARY:222222222
DTSTART;VALUE="DATE":20050701
DTEND;VALUE=DATE:20050701
ATTENDEE;RSVP=TRUE;MEMBER="mailto:DEV-GROUP@host2.com":mailto:jdoe@itaapy.com
PRIORITY:2
SEQUENCE:0
END:VEVENT
END:VCALENDAR
"""


class icalTestCase(unittest.TestCase):

    def setUp(self):
        self.cal1 = iCalendar(string=content)
        self.cal2 = iCalendar(string=content2)


    def test_new(self):
        """Test new"""
        cal = iCalendar()

        properties = []
        for name in cal.properties:
            params = cal.properties[name].parameters
            value = cal.properties[name].value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        # Test properties
        expected_properties = [
            u'VERSION;{}:2.0',
            u'PRODID;{}:-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN']
        self.assertEqual(properties, expected_properties)

        # Test components
        self.assertEqual(len(cal.get_components()), 0)
        self.assertEqual(cal.get_components('VEVENT'), [])


    def test_property(self):
        """Test to create, access and encode a property with or without
        parameters.
        """
        # Property without parameter
        expected = ['SUMMARY:This is the summary\n']

        property_value = Property('This is the summary')
        output = self.cal1.encode_property('SUMMARY', property_value)
        self.assertEqual(output, expected)

        # Property with one parameter
        expected = ['ATTENDEE;MEMBER="mailto:DEV-GROUP@host.com":'
                    'mailto:darwin@itaapy.com\n']

        params = {'MEMBER': ['"mailto:DEV-GROUP@host.com"']}
        value = Property('mailto:darwin@itaapy.com', params)
        output = self.cal1.encode_property('ATTENDEE', value)
        self.assertEqual(output, expected)


    def test_get_property_values(self):
        cal = self.cal1

        # icalendar property
        expected = '2.0'
        property = cal.get_property_values('VERSION')
        self.assertEqual(property.value, expected)

        # Component property
        events = cal.get_components('VEVENT')
        properties = events[0].get_version()

        expected = u'Résumé'
        property = events[0].get_property_values('SUMMARY')
        self.assertEqual(property.value, expected)

        expected = 1
        property = events[0].get_property_values('PRIORITY')
        self.assertEqual(property.value, expected)

        # Component properties
        properties = {}
        properties['MYADD'] = Property(u'Résumé à crêtes')
        value = Property(u'Property added by calling add_property')
        properties['DESCRIPTION'] = value
        param = '"mailto:DEV-GROUP@host2.com"'
        value = Property('mailto:darwin@itaapy.com', {'MEMBER': [param]})
        properties['ATTENDEE'] = value
        uid = cal.add_component('VEVENT', **properties)

        event = cal.get_component_by_uid(uid)
        properties = event.get_property_values()
        self.assertEqual('MYADD' in properties, True)
        self.assertEqual('DESCRIPTION' in properties, True)
        self.assertEqual('ATTENDEE' in properties, True)
        self.assertEqual('VERSION' in properties, False)


    def test_add_to_calendar(self):
        """
        Test to add property and component to an empty icalendar object.
        """
        cal = iCalendar()
        cal.add_component('VEVENT')
        self.assertEqual(len(cal.get_components('VEVENT')), 1)

        value = Property('PUBLISH')
        cal.set_property('METHOD', value)
        self.assertEqual(cal.get_property_values('METHOD'), value)


    def property_to_string(self, prop_name, prop):
        """
        Method only used by test_load and test_load2.
        """
        value, params = prop.value, ''
        for param_name in prop.parameters:
            param_value = prop.parameters[param_name]
            param = u';' + param_name +  u'=' + u','.join(param_value)
            params = params + param
        return u'%s%s:%s' % (prop_name, params, value)


    def test_load(self):
        """Test loading a simple calendar."""
        cal = self.cal1

        # Test icalendar properties
        properties = []
        for name in cal.properties:
            property_value = cal.properties[name]
            # Only property METHOD can occur several times, we give only one
            if isinstance(property_value, list):
                property_value = property_value[0]
            params = property_value.parameters
            value = property_value.value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        expected_properties = [
            u'VERSION;{}:2.0',
            u'METHOD;{}:PUBLISH',
            u'PRODID;{}:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN' ]
        self.assertEqual(properties, expected_properties)

        # Test component properties
        properties = []
        event = cal.get_components('VEVENT')[0]
        version = event.get_version()
        for prop_name in version:
            datatype = cal.get_datatype(prop_name)
            if datatype.multiple is False:
                prop = version[prop_name]
                property = self.property_to_string(prop_name, prop)
                properties.append(property)
            else:
                for prop in version[prop_name]:
                    property = self.property_to_string(prop_name, prop)
                    properties.append(property)

        expected_event_properties = [
            u'STATUS:TENTATIVE',
            u'DTSTAMP:2005-06-01 07:46:04',
            u'DESCRIPTION:all all all',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ';RSVP=TRUE:mailto:jdoe@itaapy.com',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ':mailto:jsmith@itaapy.com',
            u'SUMMARY:Résumé',
            u'PRIORITY:1',
            u'LOCATION:France',
            u'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            u'DTEND;VALUE=DATE:2005-05-31 00:00:00',
            u'DTSTART;VALUE="DATE":2005-05-30 00:00:00',
            u'CLASS:PRIVATE']

        self.assertEqual(event.uid, '581361a0-1dd2-11b2-9a42-bd3958eeac9a')
        self.assertEqual(properties, expected_event_properties)
        self.assertEqual(len(cal.get_components('VEVENT')), 1)

        # Test journals
        self.assertEqual(len(cal.get_components('VJOURNAL')), 0)
        # Test todos
        self.assertEqual(len(cal.get_components('TODO')), 0)
        # Test freebusys
        self.assertEqual(len(cal.get_components('FREEBUSY')), 0)
        # Test timezones
        self.assertEqual(len(cal.get_components('TIMEZONE')), 0)
        # Test others
        self.assertEqual(len(cal.get_components('others')), 0)


    def test_load_2(self):
        """Test loading a 2 events calendar."""
        cal = self.cal2

        properties = []
        for name in cal.properties:
            params = cal.properties[name].parameters
            value = cal.properties[name].value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        # Test properties
        expected_properties = [
            u'VERSION;{}:2.0',
            u'METHOD;{}:PUBLISH',
            u'PRODID;{}:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN' ]
        self.assertEqual(properties, expected_properties)

        events = []
        for event in cal.get_components('VEVENT'):
            version = event.get_version()

            properties = []
            for prop_name in version:
                if prop_name == 'DTSTAMP':
                    continue
                datatype = cal.get_datatype(prop_name)
                if datatype.multiple is False:
                    prop = version[prop_name]
                    property = self.property_to_string(prop_name, prop)
                    properties.append(property)
                else:
                    for prop in version[prop_name]:
                        property = self.property_to_string(prop_name, prop)
                        properties.append(property)

            events.append(properties)

        # Test events
        expected_events = [[
            u'STATUS:TENTATIVE',
            u'DESCRIPTION:all all all',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ';RSVP=TRUE:mailto:jdoe@itaapy.com',
            u'SUMMARY:Refound',
            u'PRIORITY:1',
            u'LOCATION:France',
            u'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            u'DTEND;VALUE=DATE:2005-05-31 23:59:59.999999',
            u'DTSTART;VALUE="DATE":2005-05-30 00:00:00',
            u'CLASS:PRIVATE'],
            [
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com";RSVP=TRUE'\
             ':mailto:jdoe@itaapy.com',
            u'SUMMARY:222222222',
            u'PRIORITY:2',
            u'DTEND;VALUE=DATE:2005-07-01 00:00:00',
            u'DTSTART;VALUE="DATE":2005-07-01 00:00:00'
            ]]

        self.assertEqual(events, expected_events)
        self.assertEqual(len(cal.get_components('VEVENT')), 2)

        # Test journals
        self.assertEqual(len(cal.get_components('VJOURNAL')), 0)
        # Test todos
        self.assertEqual(len(cal.get_components('TODO')), 0)
        # Test freebusys
        self.assertEqual(len(cal.get_components('FREEBUSY')), 0)
        # Test timezones
        self.assertEqual(len(cal.get_components('TIMEZONE')), 0)
        # Test others
        self.assertEqual(len(cal.get_components('others')), 0)


    # Just call to_str method
    def test_to_str(self):
        """Call to_str method."""
        cal = self.cal2
        cal.to_str()


    def test_add_property(self):
        """ Test adding a property to any component """
        cal = self.cal2
        event = cal.get_components('VEVENT')[1]

        # other property (MYADD)
        name, value = 'MYADD', Property(u'Résumé à crêtes')
        cal.update_component(event.uid, **{name: value})

        property = event.get_property_values(name)
        self.assertEqual(property[0], value)
        self.assertEqual(property[0].value, value.value)

        # property DESCRIPTION
        name = 'DESCRIPTION'
        value = Property(u'Property added by calling add_property')
        cal.update_component(event.uid, **{name: value})

        property = event.get_property_values(name)
        self.assertEqual(property, value)

        # property ATTENDEE
        name = 'ATTENDEE'
        value = event.get_property_values(name)
        param = ['"mailto:DEV-GROUP@host2.com"']
        value.append(Property('mailto:darwin@itaapy.com', {'MEMBER': param}))
        cal.update_component(event.uid, **{name: value})

        property = event.get_property_values(name)
        self.assertEqual(str(property[0].value), 'mailto:jdoe@itaapy.com')
        self.assertEqual(property[1].parameters, {'MEMBER': param})
        self.assertEqual(property[1], value[1])


    def test_icalendar_set_property(self):
        """ Test setting a new value to an existant icalendar property"""
        cal = self.cal1

        name, value = 'VERSION', Property('2.1')
        cal.set_property(name, value)
        self.assertEqual(cal.get_property_values(name), value)

        cal.set_property(name, [value, ])
        self.assertEqual(cal.get_property_values(name), value)


    def test_component_set_property(self):
        """ Test setting a new value to an existant component property"""
        cal = self.cal1
        event = cal.get_components('VEVENT')[0]

        name, value = 'SUMMARY', Property('This is a new summary')
        cal.update_component(event.uid, **{name: value})
        self.assertEqual(event.get_property_values(name), value)

        name, value = 'ATTENDEE', []
        param = ['"mailto:DEV-GROUP@host2.com"']
        value.append(Property(URI.decode('mailto:darwin@itaapy.com'),
                              {'MEMBER': param}))
        value.append(Property(URI.decode('mailto:jdoe@itaapy.com')))
        value.append(Property(URI.decode('mailto:jsmith@itaapy.com')))
        cal.update_component(event.uid, **{name: value})
        self.assertEqual(event.get_property_values(name), value)


    def test_search_events(self):
        """Test get events filtered by arguments given."""
        # Test with 1 event
        cal = self.cal1
        attendee_value = URI.decode('mailto:jdoe@itaapy.com')

        events = cal.search_events(ATTENDEE=attendee_value)
        self.assertEqual(len(events), 1)

        events = cal.search_events(STATUS='CONFIRMED')
        self.assertEqual(events, [])

        events = cal.search_events(STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(ATTENDEE=attendee_value, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(STATUS='TENTATIVE', PRIORITY=1)
        self.assertEqual(len(events), 1)

        events = cal.search_events(
            ATTENDEE=[attendee_value, URI.decode('mailto:jsmith@itaapy.com')],
            STATUS='TENTATIVE',
            PRIORITY=1)
        self.assertEqual(len(events), 1)

        # Tests with 2 events
        cal = self.cal2
        attendee_value = URI.decode('mailto:jdoe@itaapy.com')

        events = cal.search_events(ATTENDEE=attendee_value)
        self.assertEqual(len(events), 2)

        events = cal.search_events(STATUS='CONFIRMED')
        self.assertEqual(events, [])

        events = cal.search_events(STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(ATTENDEE=attendee_value, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(STATUS='TENTATIVE', PRIORITY=1)
        self.assertEqual(len(events), 1)

        events = cal.search_events(
            ATTENDEE=[attendee_value, URI.decode('mailto:jsmith@itaapy.com')],
            STATUS='TENTATIVE',
            PRIORITY=1)
        self.assertEqual(len(events), 1)


    def test_search_events_in_date(self):
        """Test search events by date."""
        cal = self.cal1

        date = datetime(2005, 5, 29)
        events = cal.search_events_in_date(date)
        self.assertEqual(len(events), 0)
        self.assertEqual(cal.has_event_in_date(date), False)

        date = datetime(2005, 5, 30)
        events = cal.search_events_in_date(date)
        self.assertEqual(len(events), 1)
        self.assertEqual(cal.has_event_in_date(date), True)

        events = cal.search_events_in_date(date, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_date(date, STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)

        attendee_value = URI.decode('mailto:jdoe@itaapy.com')
        events = cal.search_events_in_date(date, ATTENDEE=attendee_value)
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_date(date, ATTENDEE=attendee_value,
                                                 STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_date(date, ATTENDEE=attendee_value,
                                                 STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)

        date = datetime(2005, 7, 30)
        events = cal.search_events_in_date(date)
        self.assertEqual(len(events), 0)
        self.assertEqual(cal.has_event_in_date(date), False)


    def test_search_events_in_range(self):
        """Test search events matching given dates range."""
        cal = self.cal2

        dtstart = datetime(2005, 1, 1)
        dtend = datetime(2005, 1, 1, 20, 0)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 0)

        dtstart = datetime(2005, 5, 28)
        dtend = datetime(2005, 5, 30, 0, 50)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 29)
        dtend = datetime(2005, 5, 30, 0, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 30, 23, 59, 59)
        dtend = datetime(2005, 5, 31, 0, 0)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 1)
        dtend = datetime(2005, 8, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 2)

        dtstart = datetime(2005, 5, 30, 23)
        dtend = datetime(2005, 6, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 31, 0, 0, 1)
        dtend = datetime(2005, 6, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        events = cal.search_events_in_range(dtstart, dtend, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_range(dtstart, dtend, STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)

        attendee_value = URI.decode('mailto:jdoe@itaapy.com')
        events = cal.search_events_in_range(dtstart, dtend,
                                            ATTENDEE=attendee_value)
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_range(dtstart, dtend,
                                  ATTENDEE=attendee_value, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_range(dtstart, dtend,
                                  ATTENDEE=attendee_value, STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)


    def test_get_conflicts(self):
        """
        Test get_conflicts method which returns uid couples of events
        conflicting on a given date.
        """
        cal = self.cal2
        date = datetime(2005, 05, 30)

        conflicts = cal.get_conflicts(date)
        self.assertEqual(conflicts, None)

        # Set a conflict
        uid1 = '581361a0-1dd2-11b2-9a42-bd3958eeac9a'
        uid2 = '581361a0-1dd2-11b2-9a42-bd3958eeac9b'
        cal.update_component(uid2, DTSTART=Property(datetime(2005, 05, 30)),
                             DTEND=Property(datetime(2005, 05, 31)))

        conflicts = cal.get_conflicts(date)
        self.assertEqual(conflicts, [(uid1, uid2)])



class icalTableTestCase(unittest.TestCase):

    def setUp(self):
        src = iCalendar(string=content)
        src = StringIO(src.to_str())
        cal = icalendarTable()
        cal.load_state_from_ical_file(src)
        self.cal1 = cal

        src = iCalendar(string=content2)
        src = StringIO(src.to_str())
        cal = icalendarTable()
        cal.load_state_from_ical_file(src)
        self.cal2 = cal


    def test_new(self):
        """Test new"""
        cal = icalendarTable()

        properties = []
        for name in cal.properties:
            params = cal.properties[name].parameters
            value = cal.properties[name].value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        # Test properties
        expected_properties = [
            u'VERSION;{}:2.0',
            u'PRODID;{}:-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN']
        self.assertEqual(properties, expected_properties)

        # Test components
        self.assertEqual(len(cal.get_components()), 0)
        self.assertEqual(cal.get_components('VEVENT'), [])


    def test_property(self):
        """Test to create, access and encode a property with or without
        parameters.
        """
        # Property without parameter
        expected = ['SUMMARY:This is the summary\n']

        property_value = Property('This is the summary')
        output = self.cal1.encode_property('SUMMARY', property_value)
        self.assertEqual(output, expected)

        # Property with one parameter
        expected = ['ATTENDEE;MEMBER="mailto:DEV-GROUP@host.com":'
                    'mailto:darwin@itaapy.com\n']

        params = {'MEMBER': ['"mailto:DEV-GROUP@host.com"']}
        value = Property('mailto:darwin@itaapy.com', params)
        output = self.cal1.encode_property('ATTENDEE', value)
        self.assertEqual(output, expected)


    def test_get_property(self):
        cal = self.cal1

        # icalendar property
        expected = '2.0'
        property = cal.get_property('VERSION')
        self.assertEqual(property.value, expected)

        # Component property
        events = cal.get_components('VEVENT')
        properties = events[0][-1]

        expected = u'Résumé'
        property = events[0].get_property('SUMMARY')
        self.assertEqual(property.value, expected)

        expected = 1
        property = events[0].get_property('PRIORITY')
        self.assertEqual(property.value, expected)

        # Component properties
        properties = {}
        properties['MYADD'] = Property(u'Résumé à crêtes')
        value = Property(u'Property added by calling add_property')
        properties['DESCRIPTION'] = value
        param = '"mailto:DEV-GROUP@host2.com"'
        value = Property('mailto:darwin@itaapy.com', {'MEMBER': [param]})
        properties['ATTENDEE'] = value
        properties['type'] = 'VEVENT'
        uid = cal.add_record(properties).UID

        event = cal.get_component_by_uid(uid)[0]
        properties = event.get_property()
        self.assertEqual('MYADD' in properties, True)
        self.assertEqual('DESCRIPTION' in properties, True)
        self.assertEqual('ATTENDEE' in properties, True)
        self.assertEqual('VERSION' in properties, False)


    def test_add_to_calendar(self):
        """
        Test to add property and component to an empty icalendar object.
        """
        cal = icalendarTable()
        cal.add_record({'type': 'VEVENT'})
        self.assertEqual(len(cal.get_components('VEVENT')), 1)

        value = Property('PUBLISH')
        cal.set_property('METHOD', value)
        self.assertEqual(cal.get_property('METHOD'), value)


    def property_to_string(self, prop_name, prop):
        """
        Method only used by test_load and test_load2.
        """
        value, params = prop.value, ''
        for param_name in prop.parameters:
            param_value = prop.parameters[param_name]
            param = u';' + param_name +  u'=' + u','.join(param_value)
            params = params + param
        return u'%s%s:%s' % (prop_name, params, value)


    def test_load(self):
        """Test loading a simple calendar."""
        cal = self.cal1

        # Test icalendar properties
        properties = []
        for name in cal.properties:
            property_value = cal.properties[name]
            # Only property METHOD can occur several times, we give only one
            if isinstance(property_value, list):
                property_value = property_value[0]
            params = property_value.parameters
            value = property_value.value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        expected_properties = [
            u'VERSION;{}:2.0',
            u'METHOD;{}:PUBLISH',
            u'PRODID;{}:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN' ]
        self.assertEqual(properties, expected_properties)

        # Test component properties
        properties = []
        event = cal.get_components('VEVENT')[0]
        version = event[-1]
        for prop_name in version:
            if prop_name in ('ts', 'id', 'type', 'UID', 'SEQUENCE'):
                continue
            datatype = cal.get_datatype(prop_name)
            if getattr(datatype, 'multiple', False) is False:
                prop = version[prop_name]
                property = self.property_to_string(prop_name, prop)
                properties.append(property)
            else:
                for prop in version[prop_name]:
                    property = self.property_to_string(prop_name, prop)
                    properties.append(property)

        expected_event_properties = [
            u'STATUS:TENTATIVE',
            u'DTSTAMP:2005-06-01 07:46:04',
            u'DESCRIPTION:all all all',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ';RSVP=TRUE:mailto:jdoe@itaapy.com',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ':mailto:jsmith@itaapy.com',
            u'SUMMARY:Résumé',
            u'PRIORITY:1',
            u'LOCATION:France',
            u'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            u'DTEND;VALUE=DATE:2005-05-31 00:00:00',
            u'DTSTART;VALUE="DATE":2005-05-30 00:00:00',
            u'CLASS:PRIVATE']

        self.assertEqual(event.UID, '581361a0-1dd2-11b2-9a42-bd3958eeac9a')
        self.assertEqual(properties, expected_event_properties)
        self.assertEqual(len(cal.get_components('VEVENT')), 1)

        # Test journals
        self.assertEqual(len(cal.get_components('VJOURNAL')), 0)
        # Test todos
        self.assertEqual(len(cal.get_components('TODO')), 0)
        # Test freebusys
        self.assertEqual(len(cal.get_components('FREEBUSY')), 0)
        # Test timezones
        self.assertEqual(len(cal.get_components('TIMEZONE')), 0)
        # Test others
        self.assertEqual(len(cal.get_components('others')), 0)


    def test_load_2(self):
        """Test loading a 2 events calendar."""
        cal = self.cal2

        properties = []
        for name in cal.properties:
            params = cal.properties[name].parameters
            value = cal.properties[name].value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        # Test properties
        expected_properties = [
            u'VERSION;{}:2.0',
            u'METHOD;{}:PUBLISH',
            u'PRODID;{}:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN' ]
        self.assertEqual(properties, expected_properties)

        events = []
        for event in cal.get_components('VEVENT'):
            version = event[-1]

            properties = []
            for prop_name in version:
                if prop_name in ('ts', 'id', 'type', 'UID', 'SEQUENCE'):
                    continue
                if prop_name == 'DTSTAMP':
                    continue
                datatype = cal.get_datatype(prop_name)
                if getattr(datatype, 'multiple', False) is False:
                    prop = version[prop_name]
                    property = self.property_to_string(prop_name, prop)
                    properties.append(property)
                else:
                    for prop in version[prop_name]:
                        property = self.property_to_string(prop_name, prop)
                        properties.append(property)

            events.append(properties)

        # Test events
        expected_events = [[
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com";RSVP=TRUE'\
             ':mailto:jdoe@itaapy.com',
            u'SUMMARY:222222222',
            u'PRIORITY:2',
            u'DTEND;VALUE=DATE:2005-07-01 00:00:00',
            u'DTSTART;VALUE="DATE":2005-07-01 00:00:00'
            ],
            [
            u'STATUS:TENTATIVE',
            u'DESCRIPTION:all all all',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ';RSVP=TRUE:mailto:jdoe@itaapy.com',
            u'SUMMARY:Refound',
            u'PRIORITY:1',
            u'LOCATION:France',
            u'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            u'DTEND;VALUE=DATE:2005-05-31 23:59:59.999999',
            u'DTSTART;VALUE="DATE":2005-05-30 00:00:00',
            u'CLASS:PRIVATE']
            ]

        self.assertEqual(events, expected_events)
        self.assertEqual(len(cal.get_components('VEVENT')), 2)

        # Test journals
        self.assertEqual(len(cal.get_components('VJOURNAL')), 0)
        # Test todos
        self.assertEqual(len(cal.get_components('TODO')), 0)
        # Test freebusys
        self.assertEqual(len(cal.get_components('FREEBUSY')), 0)
        # Test timezones
        self.assertEqual(len(cal.get_components('TIMEZONE')), 0)
        # Test others
        self.assertEqual(len(cal.get_components('others')), 0)


    # Just call to_ical method
    def test_to_ical(self):
        """Call to_ical method."""
        cal = self.cal2
        cal.to_ical()


    def test_add_property(self):
        """ Test adding a property to any component """
        cal = self.cal2
        event = cal.get_components('VEVENT')[1]

        # other property (MYADD)
        name, value = 'MYADD', Property(u'Résumé à crêtes')
        cal.update_record(event.id, **{name: value})

        property = event.get_property(name)
        self.assertEqual(property[0], value)
        self.assertEqual(property[0].value, value.value)

        # property DESCRIPTION
        name = 'DESCRIPTION'
        value = Property(u'Property added by calling add_property')
        cal.update_record(event.id, **{name: value})

        property = event.get_property(name)
        self.assertEqual(property, value)

        # property ATTENDEE
        name = 'ATTENDEE'
        value = event.get_property(name)
        param = ['"mailto:DEV-GROUP@host2.com"']
        value.append(Property('mailto:darwin@itaapy.com',
                              {'MEMBER': param}))
        cal.update_record(event.id, **{name: value})

        property = event.get_property(name)
        self.assertEqual(str(property[0].value), 'mailto:jdoe@itaapy.com')
        self.assertEqual(property[1].parameters, {'MEMBER': param})
        self.assertEqual(property[1], value[1])


    def test_icalendar_set_property(self):
        """ Test setting a new value to an existant icalendar property"""
        cal = self.cal1

        name, value = 'VERSION', Property('2.1')
        cal.set_property(name, value)
        self.assertEqual(cal.get_property(name), value)

        name, value = 'X-test', Property('test property_xxx')
        cal.set_property(name, [value, ])
        self.assertEqual(cal.get_property(name), [value, ])


    def test_component_set_property(self):
        """ Test setting a new value to an existant component property"""
        cal = self.cal1
        event = cal.get_components('VEVENT')[0]

        name, value = 'SUMMARY', Property('This is a new summary')
        cal.update_record(event.id, **{name: value})
        self.assertEqual(event.get_property(name), value)

        name, value = 'ATTENDEE', []
        param = ['"mailto:DEV-GROUP@host2.com"']
        value.append(Property(URI.decode('mailto:darwin@itaapy.com'),
                              {'MEMBER': param}))
        value.append(Property(URI.decode('mailto:jdoe@itaapy.com')))
        value.append(Property(URI.decode('mailto:jsmith@itaapy.com')))
        cal.update_record(event.id, **{name: value})
        self.assertEqual(event.get_property(name), value)


    def test_search_events(self):
        """Test get events filtered by arguments given."""
        cal = self.cal1
        # Test with 1 event
        attendee_value = URI.decode('mailto:jdoe@itaapy.com')

        events = cal.search_events(ATTENDEE=attendee_value)
        self.assertEqual(len(events), 1)

        events = cal.search_events(STATUS='CONFIRMED')
        self.assertEqual(events, [])

        events = cal.search_events(STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(ATTENDEE=attendee_value, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(STATUS='TENTATIVE', PRIORITY=1)
        self.assertEqual(len(events), 1)

        events = cal.search_events(
            ATTENDEE=[attendee_value, URI.decode('mailto:jsmith@itaapy.com')],
            STATUS='TENTATIVE',
            PRIORITY=1)
        self.assertEqual(len(events), 1)

        # Tests with 2 events
        cal = iCalendar(string=content2)
        attendee_value = URI.decode('mailto:jdoe@itaapy.com')

        events = cal.search_events(ATTENDEE=attendee_value)
        self.assertEqual(len(events), 2)

        events = cal.search_events(STATUS='CONFIRMED')
        self.assertEqual(events, [])

        events = cal.search_events(STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(ATTENDEE=attendee_value, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)

        events = cal.search_events(STATUS='TENTATIVE', PRIORITY=1)
        self.assertEqual(len(events), 1)

        events = cal.search_events(
            ATTENDEE=[attendee_value, URI.decode('mailto:jsmith@itaapy.com')],
            STATUS='TENTATIVE',
            PRIORITY=1)
        self.assertEqual(len(events), 1)


    def test_search_events_in_date(self):
        """Test search events by date."""
        cal = self.cal1

        date = datetime(2005, 5, 29)
        events = cal.search_events_in_date(date)
        self.assertEqual(len(events), 0)
        self.assertEqual(cal.has_event_in_date(date), False)

        date = datetime(2005, 5, 30)
        events = cal.search_events_in_date(date)
        self.assertEqual(len(events), 1)
        self.assertEqual(cal.has_event_in_date(date), True)

        events = cal.search_events_in_date(date, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_date(date, STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)

        attendee_value = URI.decode('mailto:jdoe@itaapy.com')
        events = cal.search_events_in_date(date, ATTENDEE=attendee_value)
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_date(date, ATTENDEE=attendee_value,
                                                 STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_date(date, ATTENDEE=attendee_value,
                                                 STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)

        date = datetime(2005, 7, 30)
        events = cal.search_events_in_date(date)
        self.assertEqual(len(events), 0)
        self.assertEqual(cal.has_event_in_date(date), False)


    def test_search_events_in_range(self):
        """Test search events matching given dates range."""
        cal = self.cal2

        dtstart = datetime(2005, 1, 1)
        dtend = datetime(2005, 1, 1, 20, 0)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 0)

        dtstart = datetime(2005, 5, 28)
        dtend = datetime(2005, 5, 30, 0, 50)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 29)
        dtend = datetime(2005, 5, 30, 0, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 30, 23, 59, 59)
        dtend = datetime(2005, 5, 31, 0, 0)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 1)
        dtend = datetime(2005, 8, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 2)

        dtstart = datetime(2005, 5, 30, 23)
        dtend = datetime(2005, 6, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 31, 0, 0, 1)
        dtend = datetime(2005, 6, 1)
        events = cal.search_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        events = cal.search_events_in_range(dtstart, dtend, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_range(dtstart, dtend, STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)

        attendee_value = URI.decode('mailto:jdoe@itaapy.com')
        events = cal.search_events_in_range(dtstart, dtend,
                                            ATTENDEE=attendee_value)
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_range(dtstart, dtend,
                                  ATTENDEE=attendee_value, STATUS='TENTATIVE')
        self.assertEqual(len(events), 1)
        events = cal.search_events_in_range(dtstart, dtend,
                                  ATTENDEE=attendee_value, STATUS='CONFIRMED')
        self.assertEqual(len(events), 0)


    def test_get_conflicts(self):
        """
        Test get_conflicts method which returns uid couples of events
        conflicting on a given date.
        """
        cal = self.cal2
        date = datetime(2005, 05, 30)

        conflicts = cal.get_conflicts(date)
        self.assertEqual(conflicts, None)

        # Set a conflict
        uid1 = 0
        uid2 = 1
        cal.update_record(uid1, DTSTART=Property(datetime(2005, 05, 30)),
                                DTEND=Property(datetime(2005, 05, 31)))

        conflicts = cal.get_conflicts(date)
        self.assertEqual(conflicts, [(uid1, uid2)])


if __name__ == '__main__':
    unittest.main()
