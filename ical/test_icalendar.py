# -*- coding: ISO-8859-1 -*-
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


# Import from Python
import sys, os, unittest
from pprint import pprint
from datetime import datetime

# To enable to have tests in a test folder
sys.path.insert(1, os.getcwd())
sys.path.insert(1, '/'.join(os.getcwd().split('/')[:-1]))

# Import from itools
from itools.resources import get_resource
from itools.resources import memory
from itools.handlers.Text import Text
from itools.datatypes import URI

# Import from ical
from icalendar import icalendar, Property
from icalendar import unfold_lines
from itools.ical import types as icalTypes
from itools.ical.types import PropertyType, ParameterType, ComponentType

# Example with 1 event
content = """ 
BEGIN:VCALENDAR
VERSION
 :2.0
PRODID
 :-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN
METHOD
 :PUBLISH
BEGIN:VEVENT
UID
 :581361a0-1dd2-11b2-9a42-bd3958eeac9a
SUMMARY
 :Résumé
DESCRIPTION
 :all all all
LOCATION
 :France
STATUS
 :TENTATIVE
CLASS
 :PRIVATE
X-MOZILLA-RECUR-DEFAULT-INTERVAL
 :0
DTSTART
 ;VALUE="DATE"
 :20050530
DTEND
 ;VALUE=DATE
 :20050531
DTSTAMP
 :20050601T074604Z
ATTENDEE
 ;RSVP=TRUE
 ;MEMBER="MAILTO:DEV-GROUP@host2.com"
 :MAILTO:jdoe@itaapy.com
ATTENDEE
 ;MEMBER="MAILTO:DEV-GROUP@host2.com"
 :MAILTO:jsmith@itaapy.com
PRIORITY
 :1
END:VEVENT
BEGIN:VCALENDAR
"""

# Example with 2 events
content2 = """ 
BEGIN:VCALENDAR
VERSION
 :2.0
PRODID
 :-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN
METHOD
 :PUBLISH
BEGIN:VEVENT
UID
 :581361a0-1dd2-11b2-9a42-bd3958eeac9a
SUMMARY
 :Refound
DESCRIPTION
 :all all all
LOCATION
 :France
STATUS
 :TENTATIVE
CLASS
 :PRIVATE
X-MOZILLA-RECUR-DEFAULT-INTERVAL
 :0
DTSTART
 ;VALUE="DATE"
 :20050530
DTEND
 ;VALUE=DATE
 :20050531
DTSTAMP
 :20050601T074604Z
ATTENDEE
 ;RSVP=TRUE
 ;MEMBER="MAILTO:DEV-GROUP@host2.com"
 :MAILTO:jdoe@itaapy.com
PRIORITY
 :1
END:VEVENT
BEGIN:VEVENT
UID
 :581361a0-1dd2-11b2-9a42-bd3958eeac9b
SUMMARY
 :222222222
DTSTART
 ;VALUE="DATE"
 :20050701
DTEND
 ;VALUE=DATE
 :20050701
ATTENDEE
 ;RSVP=TRUE
 ;MEMBER="MAILTO:DEV-GROUP@host2.com"
 :MAILTO:jdoe@itaapy.com
PRIORITY
 :2
END:VEVENT
BEGIN:VCALENDAR
"""

class icalTestCase(unittest.TestCase):

    def test_unfolding(self):
        """Test unfolding lines."""
        
        input = (
        'BEGIN:VCALENDAR\n'
        'VERSION\n'
        ' :2.0\n'
        'PRODID\n'
        ' :-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN\n'
        'BEGIN:VEVENT\n'
        'UID\n'
        ' :581361a0-1dd2-11b2-9a42-bd3958eeac9a\n'
        'X-MOZILLA-RECUR-DEFAULT-INTERVAL\n'
        ' :0\n'
        'DTSTART\n'
        ' ;VALUE=DATE\n'
        ' :20050530\n'
        'DTEND\n'
        ' ;VALUE=DATE\n'
        ' :20050531\n'
        'DTSTAMP\n'
        ' :20050601T074604Z\n'
        'DESCRIPTION\n'
        ' :opps !!! this is a really big information, ..., but does '
        'it change \n'
        ' anything in reality ?? We should see a radical change in the next \n'
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
            #print 'input:|%s|\nexpec:|%s|' % (line,expected[i])
            self.assertEqual(line, expected[i])
            i = i + 1


    def property_to_string(self, prop_name, prop):
        value, params = prop.value, ''
        for param_key in prop.parameters:
            param = u';' + prop.parameters[param_key].name + u'='
            for val in prop.parameters[param_key].values:
                param = param + val
            params = params + param
        return u'%s%s:%s' % (prop_name, params, value)


    def test_load(self):
        """Test loading a simple calendar."""

        cal = icalendar(memory.File(content))

        # Test icalendar properties
        properties = []
        for name in cal.properties:
            params = cal.properties[name].parameters
            value = cal.properties[name].value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        expected_properties = [
            u'VERSION;{}:2.0', 
            u'METHOD;{}:PUBLISH',
            u'PRODID;{}:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN' ] 
        self.assertEqual(properties, expected_properties)

        # Test component properties
        properties = []
        event = cal.get_components_of('VEVENT')[0]
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
            u'ATTENDEE;MEMBER="MAILTO:DEV-GROUP@host2.com"' 
                     ';RSVP=TRUE:mailto:jdoe@itaapy.com', 
            u'ATTENDEE;MEMBER="MAILTO:DEV-GROUP@host2.com"'
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
        self.assertEqual(len(cal.get_components_of('VEVENT')), 1)

        # Test journals
        self.assertEqual(len(cal.get_components_of('VJOURNAL')), 0)
        # Test todos
        self.assertEqual(len(cal.get_components_of('TODO')), 0)
        # Test freebusys
        self.assertEqual(len(cal.get_components_of('FREEBUSY')), 0)
        # Test timezones
        self.assertEqual(len(cal.get_components_of('TIMEZONE')), 0)
        # Test others
        self.assertEqual(len(cal.get_components_of('others')), 0)


    def test_load_2(self):
        """Test loading a 2 events calendar."""

        cal = icalendar(memory.File(content2))

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
        for event in cal.get_components_of('VEVENT'):
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
            u'ATTENDEE;MEMBER="MAILTO:DEV-GROUP@host2.com"' 
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
            u'ATTENDEE;MEMBER="MAILTO:DEV-GROUP@host2.com";RSVP=TRUE'\
             ':mailto:jdoe@itaapy.com', 
            u'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9b', 
            u'SUMMARY:222222222', 
            u'PRIORITY:2',  
            u'DTEND;VALUE=DATE:2005-07-01 00:00:00',
            u'DTSTART;VALUE="DATE":2005-07-01 00:00:00'
            ]]

        self.assertEqual(events, \
                         expected_events)
        self.assertEqual(len(cal.get_components_of('VEVENT')), 2)

        # Test journals
        self.assertEqual(len(cal.get_components_of('VJOURNAL')), 0)
        # Test todos
        self.assertEqual(len(cal.get_components_of('TODO')), 0)
        # Test freebusys
        self.assertEqual(len(cal.get_components_of('FREEBUSY')), 0)
        # Test timezones
        self.assertEqual(len(cal.get_components_of('TIMEZONE')), 0)
        # Test others
        self.assertEqual(len(cal.get_components_of('others')), 0)


    def test_get_events_filtered(self):
        """Test get events filtered by arguments given."""

        cal = icalendar(memory.File(content))

#        events = cal.get_events_filtered(ATTENDEE='MAILTO:jdoe@itaapy.com')
#        events = cal.get_events_filtered(STATUS='TENTATIVE')
#        events = cal.get_events_filtered(ATTENDEE='MAILTO:jdoe@itaapy.com', 
#                                          STATUS='TENTATIVE')
#        events = cal.get_events_filtered(STATUS='TENTATIVE', PRIORITY=[1])
        events = cal.get_events_filtered(
          ATTENDEE=[URI.decode('MAILTO:jdoe@itaapy.com'),
                    URI.decode('MAILTO:jsmith@itaapy.com')],
          STATUS='TENTATIVE', PRIORITY=[1])

        print '- events filtered : \n'
        if events:
            for name in events[0].properties:
                occurs = PropertyType.nb_occurrences(name)
                if occurs == 1:
                    value = events[0].properties[name]
                else:
                    value = events[0].properties[name][0]

                print PropertyType.encode(name, value)

        print '\n'

   
    def test_get_events_by_date(self):
        """Test get events filtered by date."""

        cal = icalendar(memory.File(content))

        date = datetime(2005, 5, 29)
        events = cal.get_events_by_date(date)
        self.assertEqual(len(events), 0)

        date = datetime(2005, 5, 30)
        events = cal.get_events_by_date(date)
        self.assertEqual(len(events), 1)

        date = datetime(2005, 7, 30)
        events = cal.get_events_by_date(date)
        self.assertEqual(len(events), 0)


    def test_get_skeleton(self):
        """Test get_skeleton"""
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
        self.assertEqual(len(cal.get_components_of('VEVENT')), 0)
        self.assertEqual(len(cal.get_components_of('TODO')), 0)
        self.assertEqual(len(cal.get_components_of('VJOURNAL')), 0)
        self.assertEqual(len(cal.get_components_of('FREEBUSY')), 0)
        self.assertEqual(len(cal.get_components_of('TIMEZONE')), 0)
        self.assertEqual(len(cal.get_components_of('others')), 0)


    def test_get_property_calendar(self):
        cal = icalendar(memory.File(content))

        expected = '2.0'
        property = cal.get_property_values('VERSION')
        self.assertEqual(property.value, expected)


    def test_get_property_component(self):
        cal = icalendar(memory.File(content))
        events = cal.get_components_of('VEVENT')
        properties = events[0].properties

        expected = u'Résumé'
        property = events[0].get_property_values('SUMMARY')
        self.assertEqual(property.value, expected)

        expected = 1
        property = events[0].get_property_values('PRIORITY')
        self.assertEqual(property.value, expected)


    # Not a test, just print
    def test_to_str(self):
        """Test get_skeleton"""
        cal = icalendar(memory.File(content2))

        print '*** Print calendar to_str() ***'
        print cal.to_str()
        print '***********************************'


    def test_ParameterType(self):
        """Test to decode a string value and 
           compare it with encode returned value
        """   
        param = ParameterType.decode(';RSVP=TRUE')
        expected = ';RSVP=TRUE'
        self.assertEqual(ParameterType.encode(param), expected)

        param = ParameterType.decode(';MEMBER="MAILTO:DEV-GROUP@host2.com"')
        expected = ';MEMBER="MAILTO:DEV-GROUP@host2.com"'
        self.assertEqual(ParameterType.encode(param), expected)


    def test_correspond_to_date(self):
        """ Test if a component corresponds to a given date. """

        cal = icalendar(memory.File(content))
        event = cal.get_components_of('VEVENT')[0]

        date = datetime(2005, 1, 1)
        self.assertEqual(event.correspond_to_date(date), False)
        date = datetime(2005, 5, 30)
        self.assertEqual(event.correspond_to_date(date), True)
        date = datetime(2005, 5, 31)
        self.assertEqual(event.correspond_to_date(date), True)
        date = datetime(2005, 12, 1)
        self.assertEqual(event.correspond_to_date(date), False)


    def test_add_property(self):
        """ Test adding a property to any component """

        cal = icalendar(memory.File(content2))
        event = cal.get_components_of('VEVENT')[1]

        name, value = 'MYADD', [u'Résumé à crêtes']
        event.add(name, value)

        property = event.get_property_values(name)
        self.assertEqual(property[0].value, value)

        name, value = 'DESCRIPTION', 'Property added by calling add_property'
        event.add(name, value)

        property = event.get_property_values(name)
        self.assertEqual(property[0].value, value)

        param = ParameterType.decode('MEMBER=MAILTO:DEV-GROUP@host2.com')
        name, value = 'ATTENDEE', 'mailto:darwin@itaapy.com'
        property = Property(name, value, {'MEMBER': param})
        event.add(name, value, param)

        property = event.get_property_values(name)
        self.assertEqual(str(property[0].value), 'mailto:jdoe@itaapy.com')
        self.assertEqual(str(property[1].value), value)


if __name__ == '__main__':
    unittest.main()
