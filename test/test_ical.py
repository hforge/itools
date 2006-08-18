# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Deram <nderam@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import os
import sys
import unittest
from datetime import datetime

# Import from itools
from itools.handlers.Text import Text
from itools.datatypes import URI
from itools.ical.icalendar import icalendar, Component
from itools.ical.icalendar import Property, PropertyValue, Parameter
from itools.ical.icalendar import unfold_lines
from itools.ical import types as icalTypes
from itools.ical.types import PropertyType, PropertyValueType
from itools.ical.types import ParameterType, ComponentType


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
DTSTART;VALUE="DATE":20050530
DTEND;VALUE=DATE:20050531
DTSTAMP:20050601T074604Z
ATTENDEE;RSVP=TRUE;MEMBER="mailto:DEV-GROUP@host2.com":mailto:jdoe@itaapy.com
PRIORITY:1
END:VEVENT
BEGIN:VEVENT
UID:581361a0-1dd2-11b2-9a42-bd3958eeac9b
SUMMARY:222222222
DTSTART;VALUE="DATE":20050701
DTEND;VALUE=DATE:20050701
ATTENDEE;RSVP=TRUE;MEMBER="mailto:DEV-GROUP@host2.com":mailto:jdoe@itaapy.com
PRIORITY:2
END:VEVENT
END:VCALENDAR
"""


class icalTestCase(unittest.TestCase):

    def test_unfolding(self):
        """Test unfolding lines."""
        input = (
            'BEGIN:VCALENDAR\n'
            'VERSION:2.0\n'
            'PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN\n'
            'BEGIN:VEVENT\n'
            'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a\n'
            'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0\n'
            'DTSTART;VALUE=DATE:20050530\n'
            'DTEND;VALUE=DATE:20050531\n'
            'DTSTAMP:20050601T074604Z\n'
            'DESCRIPTION:opps !!! this is a really big information, ..., '
            'but does it change anything \n'
            ' in reality ?? We should see a radical change in the next \n'
            ' 3 months, shouldn\'t we ???\\nAaah !!!\n' )
                  
        expected = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN',
            'BEGIN:VEVENT',
            'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a',
            'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            'DTSTART;VALUE=DATE:20050530',
            'DTEND;VALUE=DATE:20050531',
            'DTSTAMP:20050601T074604Z',
            ('DESCRIPTION:opps !!! this is a really big information, ..., but does'
             ' it change anything in reality ?? We should see a radical change in'
             ' the next 3 months, shouldn\'t we ???\\nAaah !!!') ]

        output = unfold_lines(input)

        i = 0
        for line in output:
            self.assertEqual(line, expected[i])
            i = i + 1


    def test_new(self):
        """Test new"""
        cal = icalendar()

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
        self.assertEqual(cal.get_components(), {})
        self.assertEqual(cal.get_components('VEVENT'), [])


    def test_empty_event(self):
        """
        Test to create, access and encode an event.
        """
        expected = 'BEGIN:VEVENT\nEND:VEVENT\n'
        event = Component('VEVENT')
        self.assertEqual('UID' in event.properties, True) 
        self.assertEqual(event.c_type, 'VEVENT')
        self.assertEqual(event.encoding, 'UTF-8') 


    def test_parameter(self):
        """
        Test to create, access and encode a parameter with one or more values.
        """
        # parameter with only one value
        param = Parameter('MEMBER', ['mailto:DEV-GROUP@host.com'])
        self.assertEqual(param.name, 'MEMBER')
        self.assertEqual(param.values, ['mailto:DEV-GROUP@host.com'])

        expected = 'MEMBER=mailto:DEV-GROUP@host.com'
        self.assertEqual(ParameterType.encode(param), expected)

        # parameter with more than one value
        param = Parameter('MEMBER', ['mailto:DEV-GROUP@host.com', 
                                     'mailto:NO-GROUP@host.com'])
        self.assertEqual(param.name, 'MEMBER')
        self.assertEqual(param.values, ['mailto:DEV-GROUP@host.com',
                                        'mailto:NO-GROUP@host.com'])

        expected = 'MEMBER=mailto:DEV-GROUP@host.com,mailto:NO-GROUP@host.com'
        self.assertEqual(ParameterType.encode(param), expected)

         # Same tests from decoding
        param = ParameterType.decode(expected)
        self.assertEqual(param.name, 'MEMBER')
        self.assertEqual(param.values, ['mailto:DEV-GROUP@host.com',
                                        'mailto:NO-GROUP@host.com'])


    def test_property(self):
        """
        Test to create, access and encode a property with or without parameters.
        """
        ##################################################################
        # property without parameter
        expected = 'SUMMARY:This is the summary\n'

        # no parameters builder
        property_value = PropertyValue('This is the summary')
        property = Property('SUMMARY', property_value)
        self.assertEqual(property.name, 'SUMMARY')
        self.assertEqual(property.value, property_value)
        self.assertEqual(PropertyType.encode(property.name, property), expected)

        # with parameters builder
        property = Property('SUMMARY', PropertyValue('This is the summary'))
        self.assertEqual(PropertyType.encode(property.name, property), expected)

        ##################################################################
        # property with one parameter
        expected = 'ATTENDEE;MEMBER="mailto:DEV-GROUP@host.com":'\
                   'mailto:darwin@itaapy.com\n'
        # property with one parameter
        param = Parameter('MEMBER', ['"mailto:DEV-GROUP@host.com"'])
        params = {'MEMBER': param}
        property = Property('ATTENDEE', 
                            PropertyValue('mailto:darwin@itaapy.com', params))
        self.assertEqual(PropertyType.encode(property.name, property), 
                         expected)


    def test_get_property_values(self):
        cal = icalendar()
        cal.load_state_from_string(content)

        # icalendar property
        expected = '2.0'
        property = cal.get_property_values('VERSION')
        self.assertEqual(property.value, expected)

        # Component property
        events = cal.get_components('VEVENT')
        properties = events[0].properties

        expected = u'Résumé'
        property = events[0].get_property_values('SUMMARY')
        self.assertEqual(property.value, expected)

        expected = 1
        property = events[0].get_property_values('PRIORITY')
        self.assertEqual(property.value, expected)

        # Component properties
        event = Component('VEVENT')
        name, value = 'MYADD', PropertyValue(u'Résumé à crêtes')
        event.add(Property(name, value))
        name = 'DESCRIPTION'
        value = PropertyValue(u'Property added by calling add_property')
        event.add(Property(name, value))
        name = 'ATTENDEE'
        param = ParameterType.decode('MEMBER="mailto:DEV-GROUP@host2.com"')
        value = PropertyValue('mailto:darwin@itaapy.com', {'MEMBER': param})
        event.add(Property(name, value))

        properties = event.get_property_values()
        self.assertEqual('MYADD' in properties, True)
        self.assertEqual('DESCRIPTION' in properties, True)
        self.assertEqual('ATTENDEE' in properties, True)
        self.assertEqual('VERSION' in properties, False)


    def test_add_to_calendar(self):
        """
        Test to add property and component to an empty icalendar object.
        """
        cal = icalendar()

        event = Component('VEVENT')
        cal.add(event)
        self.assertEqual(len(cal.get_components('VEVENT')), 1)

        property = Property('METHOD', PropertyValue('PUBLISH'))
        cal.add(property)
        self.assertEqual(cal.get_property_values('METHOD'), property.value)

        param = Parameter('MEMBER', ['"mailto:DEV-GROUP@host.com"'])
        self.assertRaises(ValueError, cal.add, param)


    def property_to_string(self, prop_name, prop):
        """ 
        Method only used by test_load and test_load2.
        """
        value, params = prop.value, ''
        for param_key in prop.parameters:
            param = u';' + prop.parameters[param_key].name + u'='
            for val in prop.parameters[param_key].values:
                param = param + val
            params = params + param
        return u'%s%s:%s' % (prop_name, params, value)


    def test_load(self):
        """Test loading a simple calendar."""
        cal = icalendar()
        cal.load_state_from_string(content)

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
        for prop_name in event.properties:
            occurs = PropertyType.nb_occurrences(prop_name)
            if occurs == 1:
                prop = event.properties[prop_name]
                property = self.property_to_string(prop_name, prop)
                properties.append(property)
            else:
                for prop in event.properties[prop_name]:
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
            u'CLASS:PRIVATE', 
            u'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a']

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
        cal = icalendar()
        cal.load_state_from_string(content2)

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
            properties = []

            for prop_name in event.properties:
                occurs = PropertyType.nb_occurrences(prop_name)
                if occurs == 1:
                    prop = event.properties[prop_name]
                    property = self.property_to_string(prop_name, prop)
                    properties.append(property)
                else:
                    for prop in event.properties[prop_name]:
                        property = self.property_to_string(prop_name, prop)
                        properties.append(property)

            events.append(properties)

        # Test events
        expected_events = [[
            u'STATUS:TENTATIVE', 
            u'DTSTAMP:2005-06-01 07:46:04',  
            u'DESCRIPTION:all all all', 
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"' 
                     ';RSVP=TRUE:mailto:jdoe@itaapy.com', 
            u'SUMMARY:Refound', 
            u'PRIORITY:1', 
            u'LOCATION:France', 
            u'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0', 
            u'DTEND;VALUE=DATE:2005-05-31 00:00:00', 
            u'DTSTART;VALUE="DATE":2005-05-30 00:00:00', 
            u'CLASS:PRIVATE', 
            u'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a'], 
            [
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com";RSVP=TRUE'\
             ':mailto:jdoe@itaapy.com', 
            u'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9b', 
            u'SUMMARY:222222222', 
            u'PRIORITY:2',  
            u'DTEND;VALUE=DATE:2005-07-01 00:00:00',
            u'DTSTART;VALUE="DATE":2005-07-01 00:00:00'
            ]]

        self.assertEqual(events, \
                         expected_events)
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
        cal = icalendar()
        cal.load_state_from_string(content2)
        cal.to_str()


    def test_add_property(self):
        """ Test adding a property to any component """
        cal = icalendar()
        cal.load_state_from_string(content2)
        event = cal.get_components('VEVENT')[1]

        # other property (MYADD)
        name, value = 'MYADD', PropertyValue(u'Résumé à crêtes')
        property = Property(name, value)
        event.add(property)

        property = event.get_property_values(name)
        self.assertEqual(property[0], value)
        self.assertEqual(property[0].value, value.value)

        # property DESCRIPTION
        name = 'DESCRIPTION'
        value = PropertyValue(u'Property added by calling add_property')
        property = Property(name, value)
        event.add(property)

        property = event.get_property_values(name)
        self.assertEqual(property, value)

        # property ATTENDEE
        name = 'ATTENDEE'
        param = ParameterType.decode('MEMBER="mailto:DEV-GROUP@host2.com"')
        value = PropertyValue('mailto:darwin@itaapy.com', {'MEMBER': param})
        property = Property(name, value)
        event.add(property)

        property = event.get_property_values(name)
        self.assertEqual(str(property[0].value), 'mailto:jdoe@itaapy.com')
        self.assertEqual(property[1].parameters, {'MEMBER': param})
        self.assertEqual(property[1], value)


    def test_icalendar_set_property(self):
        """ Test setting a new value to an existant icalendar property"""
        cal = icalendar()
        cal.load_state_from_string(content)

        name, value = 'VERSION', PropertyValue('2.1')
        cal.set_property(name, value)
        self.assertEqual(cal.get_property_values(name), value)

        cal.set_property(name, [value, ])
        self.assertEqual(cal.get_property_values(name), value)


    def test_component_set_property(self):
        """ Test setting a new value to an existant component property"""
        cal = icalendar()
        cal.load_state_from_string(content)
        event = cal.get_components('VEVENT')[0]

        name, value = 'SUMMARY', PropertyValue('This is a new summary')
        event.set_property(name, value)
        self.assertEqual(event.get_property_values(name), value)

        name, value = 'ATTENDEE', []
        param = ParameterType.decode('MEMBER="mailto:DEV-GROUP@host2.com"')
        value.append(PropertyValue(URI.decode('mailto:darwin@itaapy.com'), 
                                   {'MEMBER': param}))
        value.append(PropertyValue(URI.decode('mailto:jdoe@itaapy.com')))
        value.append(PropertyValue(URI.decode('mailto:jsmith@itaapy.com')))
        event.set_property(name, value)
        self.assertEqual(event.get_property_values(name), value)


    def test_correspond_to_date(self):
        """ Test if a component corresponds to a given date. """
        cal = icalendar()
        cal.load_state_from_string(content)
        event = cal.get_components('VEVENT')[0]

        date = datetime(2005, 1, 1)
        self.assertEqual(event.correspond_to_date(date), False)
        date = datetime(2005, 5, 30)
        self.assertEqual(event.correspond_to_date(date), True)
        date = datetime(2005, 5, 31)
        self.assertEqual(event.correspond_to_date(date), True)
        date = datetime(2005, 12, 1)
        self.assertEqual(event.correspond_to_date(date), False)


    def test_in_range(self):
        """ Test if a component is in given dates range. """
        cal = icalendar()
        cal.load_state_from_string(content)
        event = cal.get_components('VEVENT')[0]

        dtstart = datetime(2005, 1, 1)
        dtend = datetime(2005, 1, 1, 20, 0)
        self.assertEqual(event.in_range(dtstart, dtend), False)
        dtstart = datetime(2005, 5, 28)
        dtend = datetime(2005, 5, 30, 0, 0)
        self.assertEqual(event.in_range(dtstart, dtend), False)
        dtstart = datetime(2005, 5, 29)
        dtend = datetime(2005, 5, 30, 0, 1)
        self.assertEqual(event.in_range(dtstart, dtend), True)
        dtstart = datetime(2005, 5, 30, 23, 59, 59)
        dtend = datetime(2005, 5, 31, 0, 0)
        self.assertEqual(event.in_range(dtstart, dtend), True)
        dtstart = datetime(2005, 5, 1)
        dtend = datetime(2005, 6, 1)
        self.assertEqual(event.in_range(dtstart, dtend), True)
        dtstart = datetime(2005, 5, 31)
        dtend = datetime(2005, 6, 1)
        self.assertEqual(event.in_range(dtstart, dtend), False)
        dtstart = datetime(2005, 5, 31, 0, 0, 1)
        dtend = datetime(2005, 6, 1)
        self.assertEqual(event.in_range(dtstart, dtend), False)


    def test_search_events(self):
        """Test get events filtered by arguments given."""
        # Test with 1 event
        cal = icalendar()
        cal.load_state_from_string(content)
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
        cal = icalendar()
        cal.load_state_from_string(content2)
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


    def test_get_events_in_date(self):
        """Test get events filtered by date."""
        cal = icalendar()
        cal.load_state_from_string(content)

        date = datetime(2005, 5, 29)
        events = cal.get_events_in_date(date)
        self.assertEqual(len(events), 0)
        self.assertEqual(cal.has_event_in_date(date), False)

        date = datetime(2005, 5, 30)
        events = cal.get_events_in_date(date)
        self.assertEqual(len(events), 1)
        self.assertEqual(cal.has_event_in_date(date), True)

        date = datetime(2005, 7, 30)
        events = cal.get_events_in_date(date)
        self.assertEqual(len(events), 0)
        self.assertEqual(cal.has_event_in_date(date), False)


    def test_get_events_in_range(self):
        """Test get events matching given dates range."""
        cal = icalendar()
        cal.load_state_from_string(content2)

        dtstart = datetime(2005, 1, 1)
        dtend = datetime(2005, 1, 1, 20, 0)
        events = cal.get_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 0)

        dtstart = datetime(2005, 5, 28)
        dtend = datetime(2005, 5, 30, 0, 50)
        events = cal.get_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 29)
        dtend = datetime(2005, 5, 30, 0, 1)
        events = cal.get_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 30, 23, 59, 59)
        dtend = datetime(2005, 5, 31, 0, 0)
        events = cal.get_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 1)
        dtend = datetime(2005, 8, 1)
        events = cal.get_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 2)

        dtstart = datetime(2005, 5, 30, 23)
        dtend = datetime(2005, 6, 1)
        events = cal.get_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 1)

        dtstart = datetime(2005, 5, 31, 0, 0, 1)
        dtend = datetime(2005, 6, 1)
        events = cal.get_events_in_range(dtstart, dtend)
        self.assertEqual(len(events), 0)


    def test_get_conflicts(self):
        """
        Test get_conflicts method which returns uid couples of events
        conflicting on a given date. 
        """
        cal = icalendar()
        cal.load_state_from_string(content2)
        date = datetime(2005, 05, 30)

        conflicts = cal.get_conflicts(date)
        self.assertEqual(conflicts, None) 

        # set a conflict
        uid1 = '581361a0-1dd2-11b2-9a42-bd3958eeac9a'
        uid2 = '581361a0-1dd2-11b2-9a42-bd3958eeac9b'
        event = cal.get_component_by_uid(uid2)
        name, value = 'DTSTART', PropertyValue(datetime(2005, 05, 30))
        event.set_property(name, value)
        name, value = 'DTEND', PropertyValue(datetime(2005, 05, 31))
        event.set_property(name, value)
            
        conflicts = cal.get_conflicts(date)
        self.assertEqual(conflicts, [(uid1, uid2)])


if __name__ == '__main__':
    unittest.main()
