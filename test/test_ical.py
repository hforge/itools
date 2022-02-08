# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006-2007 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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
from datetime import datetime, timedelta, tzinfo
from unittest import TestCase, main

# Import from itools
from itools.csv import Property
from itools.csv.table import encode_param_value
from itools.datatypes import String
from itools.ical import DateTime, iCalendar
from itools.ical.icalendar import iCalendar, VTimezone
#


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

tz_file_test = frozenset([
        # Input datetime         , tzname,      dst,    utcoffset
        ((1967, 4, 30, 2, 0, 1), ('EDT', (0, 3600), (-1, 72000))),
        ((1971, 12, 25, 12, 42, 00), ('EST', (0, 0), (-1, 68400))),
        ((1973, 4, 28, 6, 59, 59), ('EST', (0, 0), (-1, 68400))),
        ((1974, 4, 29, 6, 59, 59), ('EDT', (0, 3600), (-1, 72000))),
        ((1986, 2, 12, 12, 42, 0), ('EST', (0, 0), (-1, 68400))),
        ((1986, 6, 12, 12, 42, 0), ('EDT', (0, 3600), (-1, 72000))),
        ])


def property_to_string(prop_name, prop):
    """Method only used by test_load and test_load2.
    """
    # Convert DateTimes
    prop_value = prop.value
    if type(prop.value) is datetime:
        params = prop.parameters
        if params:
            t = params['VALUE'][0] if 'VALUE' in params else None
        else:
            t = None
        prop_value = DateTime.encode(prop.value, type=t)
    # Simple case
    if not prop.parameters:
        return '%s:%s' % (prop_name, prop_value)

    # Params
    params = ''
    for p_name in prop.parameters:
        p_value = prop.parameters[p_name]
        p_value = [encode_param_value(p_name, x, String) for x in p_value]
        param = ';%s=%s' % (p_name, ','.join(p_value))
        params = params + param
    return '%s%s:%s' % (prop_name, params, prop_value)



class icalTestCase(TestCase):

    def setUp(self):
        self.cal1 = iCalendar(string=content)
        self.cal2 = iCalendar(string=content2)


    def test_new(self):
        cal = iCalendar()

        properties = []
        for name in cal.properties:
            params = cal.properties[name].parameters
            value = cal.properties[name].value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        # Test properties
        expected_properties = [
            u'VERSION;None:2.0',
            u'PRODID;None:-//hforge.org/NONSGML ikaaro icalendar V1.0//EN']
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

        member = 'mailto:DEV-GROUP@host.com'
        value = Property('mailto:darwin@itaapy.com', MEMBER=[member])
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
        member = '"mailto:DEV-GROUP@host2.com"'
        value = Property('mailto:darwin@itaapy.com', MEMBER=[member])
        properties['ATTENDEE'] = value
        uid = cal.add_component('VEVENT', **properties)

        event = cal.get_component_by_uid(uid)
        properties = event.get_property_values()
        self.assertEqual('MYADD' in properties, True)
        self.assertEqual('DESCRIPTION' in properties, True)
        self.assertEqual('ATTENDEE' in properties, True)
        self.assertEqual('VERSION' in properties, False)


    def test_add_to_calendar(self):
        """Test to add property and component to an empty icalendar object.
        """
        cal = iCalendar()
        cal.add_component('VEVENT')
        self.assertEqual(len(cal.get_components('VEVENT')), 1)

        value = Property('PUBLISH')
        cal.set_property('METHOD', value)
        self.assertEqual(cal.get_property_values('METHOD'), value)


    def test_load(self):
        """Test loading a simple calendar.
        """
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
            u'VERSION;None:2.0',
            u'METHOD;None:PUBLISH',
            u'PRODID;None:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN']
        self.assertEqual(properties, expected_properties)

        # Test component properties
        properties = []
        event = cal.get_components('VEVENT')[0]
        version = event.get_version()
        for prop_name in version:
            datatype = cal.get_record_datatype(prop_name)
            if datatype.multiple is False:
                prop = version[prop_name]
                property = property_to_string(prop_name, prop)
                properties.append(property)
            else:
                for prop in version[prop_name]:
                    property = property_to_string(prop_name, prop)
                    properties.append(property)

        expected_event_properties = [
            u'STATUS:TENTATIVE',
            u'DTSTAMP:20050601T074604Z',
            u'DESCRIPTION:all all all',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ';RSVP=TRUE:mailto:jdoe@itaapy.com',
            u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     ':mailto:jsmith@itaapy.com',
            u'SUMMARY:Résumé',
            u'PRIORITY:1',
            u'LOCATION:France',
            u'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            u'DTEND;VALUE=DATE:20050531',
            u'DTSTART;VALUE=DATE:20050530',
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
        """Test loading a 2 events calendar.
        """
        cal = self.cal2

        properties = []
        for name in cal.properties:
            params = cal.properties[name].parameters
            value = cal.properties[name].value
            property = '%s;%s:%s' % (name, params, value)
            properties.append(property)

        # Test properties
        expected_properties = [
            'VERSION;None:2.0',
            'METHOD;None:PUBLISH',
            'PRODID;None:-//Mozilla.org/NONSGML Mozilla Calendar V1.0//EN' ]
        self.assertEqual(properties, expected_properties)

        events = []
        for event in cal.get_components('VEVENT'):
            version = event.get_version()

            properties = []
            for prop_name in version:
                if prop_name == 'DTSTAMP':
                    continue
                datatype = cal.get_record_datatype(prop_name)
                if datatype.multiple is False:
                    prop = version[prop_name]
                    property = property_to_string(prop_name, prop)
                    properties.append(property)
                else:
                    for prop in version[prop_name]:
                        property = property_to_string(prop_name, prop)
                        properties.append(property)

            events.append(properties)

        # Test events
        expected_events = [
            [u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com";RSVP=TRUE'
                             u':mailto:jdoe@itaapy.com',
             u'SUMMARY:222222222',
             u'PRIORITY:2',
             u'DTEND;VALUE=DATE:20050701',
             u'DTSTART;VALUE=DATE:20050701'],
            [u'STATUS:TENTATIVE',
             u'DESCRIPTION:all all all',
             u'ATTENDEE;MEMBER="mailto:DEV-GROUP@host2.com"'
                     u';RSVP=TRUE:mailto:jdoe@itaapy.com',
             u'SUMMARY:Refound',
             u'PRIORITY:1',
             u'LOCATION:France',
             u'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
             u'DTEND;VALUE=DATE:20050531',
             u'DTSTART;VALUE=DATE:20050530',
             u'CLASS:PRIVATE'],
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


    # Just call to_str method
    def test_to_str(self):
        """Call to_str method.
        """
        cal = self.cal2
        cal.to_str()


    def test_add_property(self):
        """Test adding a property to any component.
        """
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
        member = '"mailto:DEV-GROUP@host2.com"'
        value.append(Property('mailto:darwin@itaapy.com', MEMBER=[member]))
        cal.update_component(event.uid, **{name: value})

        property = event.get_property_values(name)
        self.assertEqual(str(property[0].value), 'mailto:jdoe@itaapy.com')
        self.assertEqual(property[1].parameters, {'MEMBER': [member]})
        self.assertEqual(property[1], value[1])


    def test_icalendar_set_property(self):
        """Test setting a new value to an existant icalendar property.
        """
        cal = self.cal1

        name, value = 'VERSION', Property('2.1')
        cal.set_property(name, value)
        self.assertEqual(cal.get_property_values(name), value)

        cal.set_property(name, [value, ])
        self.assertEqual(cal.get_property_values(name), value)


    def test_component_set_property(self):
        """Test setting a new value to an existant component property.
        """
        cal = self.cal1
        event = cal.get_components('VEVENT')[0]

        name, value = 'SUMMARY', Property('This is a new summary')
        cal.update_component(event.uid, **{name: value})
        self.assertEqual(event.get_property_values(name), value)

        member = '"mailto:DEV-GROUP@host2.com"'
        value = [
            Property('mailto:darwin@itaapy.com', MEMBER=[member]),
            Property('mailto:jdoe@itaapy.com'),
            Property('mailto:jsmith@itaapy.com')]
        cal.update_component(event.uid, ATTENDEE=value)
        self.assertEqual(event.get_property_values('ATTENDEE'), value)


    def test_vtimezone(self):
        handler = iCalendar('tests/test_vtimezone.ics')
        tz = handler.get_components('VTIMEZONE')
        self.assertEqual(len(tz), 1)
        tz = tz[0]
        self.assertEqual(tz.__class__, VTimezone)
        self.assertTrue(isinstance(tz, tzinfo))
        for dt, (tzname, dst, utcoffset) in tz_file_test:
            dt = datetime(*dt, tzinfo=tz)
            self.assertEqual(tz.tzname(dt), tzname)
            self.assertEqual(tz.dst(dt), timedelta(*dst))
            self.assertEqual(tz.utcoffset(dt), timedelta(*utcoffset))


if __name__ == '__main__':
    main()
