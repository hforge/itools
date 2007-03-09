# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Nicolas Deram <nderam@itaapy.com>
#               2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#               2005 Nicolas Oyez <nicoyez@gmail.com>
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

# Import from Python Standard Library
from datetime import datetime, date, time, timedelta
from copy import deepcopy
from operator import itemgetter

# Import from itools
from itools.datatypes import Unicode, String
from itools.catalog import queries
from itools.catalog.queries import Equal, Range, Or, And
from itools.handlers.Text import Text
from itools.csv.csv import Catalog
from itools.ical.types import PropertyType, data_properties


# The smallest possible difference between non-equal timedelta objects.
#
# XXX To be used to work-around the fact that range searches don't include
# the righ limit. So if we want to search a date between 'dtstart' and
# 'dtend', we must write:
#
#    Range('date', dtstart, dtend + resolution)
#
# To be used systematically. Till the day we replace Range searches by the
# more complete set: GreaterThan, GreaterThanOrEqual, LesserThan and
# LesserThanOrEqual.
resolution = timedelta.resolution



def unfold_lines(data):
    """
    Unfold the folded lines.
    """
    i = 0
    lines = data.splitlines()

    line = ''
    while i < len(lines):
        next = lines[i]
        if next.startswith(' ') or next.startswith('\t'):
            line += next[1:]
        else:
            if line:
                yield line
            line = next
        i += 1
    if line:
        yield line



class PropertyValue(object):

    def __init__(self, value, **kw):
        """
        Initialize the property value.

        value -- value as a string
        parameters -- {param1_name: Parameter object, ...}
        """
        self.value = value
        self.parameters = kw


class Component(object):
    """
    Parses and evaluates a component block.
        
        input :   string values for c_type and encoding 
                  a list of Property objects 
                  (Property objects can share the same name as a property
                  name can appear more than one time in a component)
        
        output :  string values for c_type and encoding
                  a dictionnary {'property_name': Property[] } for properties
    """
    # XXX A parse method should be added to test properties inside of current 
    # component-type/properties (for example to test if property can appear
    # more than one time, ...)

    def __init__(self, c_type, uid):
        """
        Initialize the component.

        properties -- {property1_name: Property object, ...}
        c_type -- type of component as a string (i.e. 'VEVENT')
        """
        self.c_type = c_type
        self.uid = uid
        self.versions = {}


    #######################################################################
    # API / Private
    #######################################################################
    def get_value(self, name):
        """
        Returns the value of a property if it exists. Otherwise returns None.
        """
        # Case insensitive
        name = name.upper()

        # The type
        if name == 'TYPE':
            return self.c_type

        # Get the last version
        version = self.get_version()

        # Properties
        if name not in version:
            return None

        property = version[name]
        value = property.value

        # According to the RFC, when DTEND is of format DATE, it is
        # interpreted as the event happens the whole day.
        if name == 'DTEND':
            format = property.parameters.get('VALUE')
            if format is not None and 'DATE' in format:
                value = value + timedelta(days=1) - resolution

        return value


    def get_sequences(self):
        sequences = self.versions.keys()
        sequences.sort()
        return sequences


    def add_version(self, properties):
        # Check value
        for name in properties:
            value = properties[name]

            occurs = PropertyType.nb_occurrences(name)
            if occurs != 1:
                if not isinstance(value, list):
                    properties[name] = [value]
            else:
                if isinstance(value, list):
                    if len(value) != 1:
                        raise ValueError, ('property "%s" requires only one'
                                           ' value' % name)
                    properties[name] = value[0]

        # Sequence
        if 'SEQUENCE' in properties:
            sequence = properties.pop('SEQUENCE')
            sequence = sequence.value
        else:
            sequences = self.get_sequences()
            if sequences:
                sequence = sequences[-1] + 1
            else:
                sequence = 0

        # Timestamp
        if 'DTSTAMP' not in properties:
            properties['DTSTAMP'] = PropertyValue(datetime.today())

        self.versions[sequence] = properties


    #######################################################################
    # API / Public
    #######################################################################
    def get_version(self, sequence=None):
        if sequence is None:
            sequence = self.get_sequences()[-1]
        return self.versions[sequence]


    # Get a property of current component
    def get_property_values(self, name=None):
        """
        Return the value of given name property as a PropertyValue or as a list
        of PropertyValue objects if it can occur more than once.

        Return icalendar property values as a dict {name: value, ...} where
        value is a PropertyValue or a list of PropertyValue objects if it can
        occur more than once.
        """
        version = self.get_version()
        if name:
            return version.get(name, None)
        return version



class icalendar(Text):
    """
    icalendar structure :

        BEGIN:VCALENDAR

            --properties
                     required : PRODID, VERSION
                     optionnal : CALSCALE, METHOD, non-standard ones...

            --components(min:1)
                     VEVENT, TODO, JOURNAL, FREEBUSY, TIMEZONE,
                     iana component, non-standard component...

        END:VCALENDAR
    """

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'properties', 'components', 'catalog', 'encoding']
    class_mimetypes = ['text/calendar']
    class_extension = 'ics'


    #########################################################################
    # New
    #########################################################################
    def _init_ical(self):
        self.properties = {}
        self.components = {}
        self.catalog = Catalog()
        self.catalog.add_index('type', 'keyword')
        self.catalog.add_index('dtstart', 'keyword')
        self.catalog.add_index('dtend', 'keyword')


    def new(self):
        self._init_ical()

        properties = (
            ('VERSION', {}, u'2.0'), 
            ('PRODID', {}, u'-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN')
          )
        for name, param, value in properties:
            self.properties[name] = PropertyValue(value, **param)

        # The encoding
        self.encoding = 'UTF-8'


    def _load_state_from_file(self, file):
        self._init_ical()

        data = file.read()
        encoding = Text.guess_encoding(data)
        self.encoding = encoding

        value = []
        for line in unfold_lines(data):
            # Add tuple (name, PropertyValue) to list value keeping order
            prop_name, prop_value = PropertyType.decode(line, encoding)
            value.append((prop_name, prop_value))

        status = 0
        nbproperties = 0
        optproperties = []

        if (value[0][0]!='BEGIN' or value[0][1].value!='VCALENDAR'
            or len(value[0][1].parameters)!=0): 
            raise ValueError, 'icalendar must begin with BEGIN:VCALENDAR'


        ##################################
        # GET PROPERTIES INTO properties #
        ##################################

        # Get number of properties
        for prop_name, prop_value in value[1:-1]:
            if prop_name == 'BEGIN':
                break
            nbproperties = nbproperties + 1

        # Get properties
        done = []
        for prop_name, prop_value in value[1:nbproperties+1]:
            if prop_name == 'VERSION':
                if 'VERSION' in done:
                    raise ValueError, 'VERSION can appear only one time'
                done.append('VERSION')
            if prop_name == 'PRODID':
                if 'PRODID' in done:
                    raise ValueError, 'PRODID can appear only one time'
                done.append('PRODID')
            self.properties[prop_name] = prop_value

        # Check if VERSION and PRODID properties don't miss
        if 'VERSION' not in done or 'PRODID' not in done:
            raise ValueError, 'PRODID or VERSION parameter missing'


        ########################################
        # GET COMPONENTS INTO self.<component> #
        ########################################
        c_type = None
        uid = None
 
        for prop_name, prop_value in value[nbproperties+1:-1]:
            if prop_name in ('PRODID', 'VERSION'):
                raise ValueError, 'PRODID and VERSION must appear before '\
                                  'any component'
            if c_type is None:
                if prop_name == 'BEGIN':
                    c_type = prop_value.value
                    c_properties = {}
                continue

            if prop_name == 'END':
                if prop_value.value == c_type:
                    if uid is None:
                        raise ValueError, 'UID is not present'

                    component = Component(c_type, uid)
                    component.add_version(c_properties)
                    self.components[uid] = component
                    self.catalog.index_document(component, uid)
                    # Next
                    c_type = None
                    uid = None
                #elif prop_value.value in component_list:
                #    raise ValueError, '%s component can NOT be inserted '\
                #          'into %s component' % (prop_value.value, c_type)
                else:
                    raise ValueError, 'Inner components are not managed yet'
            else:
                if prop_name == 'UID':
                    uid = prop_value.value
                elif prop_name in c_properties:
                    try:
                        c_properties[prop_name].extend(prop_value)
                    except AttributeError:
                        raise SyntaxError, ('Property %s can be assigned only'
                                            ' one value' % prop_name)
                else:
                    c_properties[prop_name] = prop_value


    def to_str(self, encoding='UTF-8'):
        lines = []

        line = 'BEGIN:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        # Calendar properties
        for key in self.properties:
            occurs = PropertyType.nb_occurrences(key) 
            if occurs == 1:
                lines.append(PropertyType.encode(key, self.properties[key]))
            else:
                for property_value in self.properties[key]:
                    lines.append(PropertyType.encode(key, property_value))
        # Calendar components
        for uid in self.components:
            component = self.components[uid]
            c_type = component.c_type
            for sequence in component.get_sequences():
                version = component.versions[sequence]
                # Serialize
                line = 'BEGIN:%s\n' % c_type
                lines.append(Unicode.encode(line))
                # UID, SEQUENCE
                lines.append('UID:%s\n' % uid)
                lines.append('SEQUENCE:%s\n' % sequence)
                # Properties
                for key in version:
                    value = version[key]
                    occurs = PropertyType.nb_occurrences(key)
                    if occurs == 1:
                        lines.append(PropertyType.encode(key, value))
                    else:
                        for item in value:
                            lines.append(PropertyType.encode(key, item))

                line = 'END:%s\n' % c_type
                lines.append(Unicode.encode(line))

        line = 'END:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        return ''.join(lines)


    #######################################################################
    # To override
    #######################################################################
    def generate_uid(self, c_type):
        return c_type +'-'+ datetime.now().strftime('%Y-%m-%d %H:%M:%S %p')


    #######################################################################
    # API
    #######################################################################
    def add_component(self, c_type, **kw):
        # Build the component
        uid = self.generate_uid(c_type)
        component = Component(c_type, uid)

        # Add the component
        self.set_changed()
        self.components[uid] = component
        component.add_version(kw)

        # Index the component
        self.catalog.index_document(component, uid)

        return uid


    def update_component(self, uid, **kw):
        # Build the new version
        component = self.components[uid]
        version = component.get_version()
        version = version.copy()
        version.update(kw)

        # Add the new version
        self.set_changed()
        component.add_version(version)

        # Index the component
        self.catalog.index_document(component, uid)


    def remove(self, uid):
        """
        Definitely remove from the calendar each occurrence of an existant
        component. 
        """
        self.set_changed()
        # Remove
        component = self.components[uid]
        del self.components[uid]
        # Unindex
        self.catalog.unindex_document(component, uid)


    def get_property_values(self, name=None):
        """
        Return PropertyValue[] for the given icalendar property name
        or
        Return icalendar property values as a dict 
            {property_name: PropertyValue object, ...}

        *searching only for general properties, not components ones.
        """
        if name:
            return self.properties.get(name, None)
        return self.properties


    def set_property(self, name, values):
        """
        Set values to the given property, removing previous ones.

        name -- name of the property as a string
        values -- PropertyValue[]
        """
        occurs = PropertyType.nb_occurrences(name)
        if occurs == 1:
            # If the property can occur only once, set the first value of the
            # list, ignoring others
            if isinstance(values, list):
                values = values[0]
        else:
            # Get a list if it is not.
            if not isinstance(values, list):
                values = [values]

        self.set_changed()
        self.properties[name] = values


    def get_components(self, type=None):
        """
        Return a dict {component_type: Component[], ...}
        or 
        Return Component[] of given type.
        """
        if type is None:
            return self.components

        return [ self.components[x] for x in self.search(type=type) ]


    # Get some events corresponding to arguments
    def search_events(self, **kw):
        """
        Return a list of Component objects of type 'VEVENT' corresponding to
        the given filters.

        It should be used like this, for example:

            events = cal.search_events(
                STATUS='TENTATIVE', 
                PRIORITY=1,
                ATTENDEE=[URI.decode('mailto:jdoe@itaapy.com'),
                          URI.decode('mailto:jsmith@itaapy.com')])

        ** With a list of values, events match if at least one value matches
        """
        res_events = []

        # Get the list of differents property names used to filter
        filters = kw.keys()

        # For each events
        for event in self.get_components(type='VEVENT'):
            version = event.get_version()

            # For each filter
            for filter in filters:
                # If filter not in component, go to next one
                if filter not in version:
                    break
                # Test filter
                expected = kw.get(filter)
                property_value = version[filter]
                occurs = PropertyType.nb_occurrences(filter) 
                if occurs == 1:
                    if property_value.value != expected:
                        break
                else:
                    for item in property_value:
                        if isinstance(expected, list):
                            if item.value in expected:
                                break
                        elif item.value == expected:
                            break
                    else:
                        break
            else:
                res_events.append(event)

        return res_events


    def get_component_by_uid(self, uid):
        """
        Return components with the given uid, None if it doesn't appear.
        """
        return self.components.get(uid)


    # Get some events corresponding to a given date
    def get_events_in_date(self, date):
        """
        Return a list of Component objects of type 'VEVENT' matching the
        given date. 
        """
        # Get only the events which match
        query = And(Equal('type', 'VEVENT'),
                    Range('dtstart', None, date + resolution),
                    Range('dtend', date, None))

        return [ self.components[x] for x in self.search(query) ]


    def get_events_in_range(self, dtstart, dtend):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        dates range. 
        """
        # Get only the events which matches
        query = And(Equal('type', 'VEVENT'),
                    Or(Range('dtstart', dtstart, dtend + resolution),
                       Range('dtend', dtstart, dtend + resolution),
                       And(Range('dtstart', None, dtstart + resolution),
                           Range('dtend', dtend, None))))

        return [ self.components[x] for x in self.search(query) ]


    def get_sorted_events_in_date(self, selected_date):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        date and sorted chronologically.
        """
        dtstart = datetime.combine(selected_date, time(0,0))
        dtend = datetime.combine(selected_date, time(23,59))

        return self.get_sorted_events_in_range(dtstart, dtend)


    def get_sorted_events_in_range(self, dtstart, dtend):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        dates range and sorted chronologically.
        """
        res_events = []

        # Check type of dates, we need datetime for method in_range
        if not isinstance(dtstart, datetime):
            dtstart = datetime(dtstart.year, dtstart.month, dtstart.day)
        if not isinstance(dtend, datetime):
            dtend = datetime(dtend.year, dtend.month, dtend.day)

        # Get only the events which matches
        query = And(Equal('type', 'VEVENT'),
                    Or(Range('dtstart', dtstart, dtend + resolution),
                       Range('dtend', dtstart, dtend + resolution),
                       And(Range('dtstart', None, dtstart + resolution),
                           Range('dtend', dtend, None))))

        for n in self.search(query):
            event = self.components[n]
            version = event.get_version()
            value = {
                'dtstart': version['DTSTART'].value,
                'dtend': version['DTEND'].value,
                'event': event
              }
            res_events.append(value)

        if len(res_events) <= 1:
            return res_events

        # Sort by dtstart
        res_events = sorted(res_events, key=itemgetter('dtstart'))
        # Sort by dtend
        last_end = res_events[0]['dtstart']
        same_start, res = [], [res_events[0]]
        for e in res_events[1:]:
            if last_end == e['dtstart']:
                same_start.append(e)
            else:
                if same_start != []:
                    res.extend(same_start)
                    same_start = []
                res.append(e)
        if same_start != []:
            res.extend(same_start)

        return res


    # Test if any event corresponds to a given date
    def has_event_in_date(self, date):
        """
        Return True if there is at least one event matching the given date.
        """
        return self.get_events_in_date(date) != []


    def get_conflicts(self, date):
        """
        Returns a list of uid couples which happen at the same time.
        We check only last occurrence of events.
        """
        events = self.get_events_in_date(date)
        if len(events) <= 1:
            return None

        conflicts = []
        # We take each event as a reference
        for i, event_ref in enumerate(events):
            version = event_ref.get_version()
            dtstart_ref = version['DTSTART'].value
            dtend_ref = version['DTEND'].value
            # For each other event, we test if there is a conflict
            for j, event in enumerate(events):
                if j <= i:
                    continue
                version = event.get_version()
                dtstart = version['DTSTART'].value
                dtend = version['DTEND'].value

                if dtstart >=  dtend_ref or dtend <= dtstart_ref:
                    continue
                conflicts.append((i, j))

        # Replace index of components by their UID
        if conflicts != []:
            for index, (i, j) in enumerate(conflicts):
                conflicts[index] = (events[i].uid, events[j].uid)

        return conflicts


    #######################################################################
    # API / Search
    def get_index(self, name):
        try:
            return self.catalog.indexes[name]
        except KeyError:
            raise ValueError, 'the field "%s" is not indexed' % name


    def search(self, query=None, **kw):
        """
        Return list of component internal ids returned by executing the query.
        """
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(queries.Equal(key, value))

                query = queries.And(*atoms)
            else:
                raise ValueError, "expected a query"

        documents = query.search(self)
        # Sort by weight
        documents = documents.keys()
        documents.sort()

        return documents

