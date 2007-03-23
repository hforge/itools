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
from itools.catalog import Equal, Range, Or, And
from itools.handlers import Text
from itools.csv import Catalog
from itools.ical.parser import parse
from itools.ical.types import data_properties, fold_line, DateTime


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



class PropertyValue(object):

    def __init__(self, value, **kw):
        """
        Initialize the property value.

        value -- value as a string
        kw    -- {param1_name: [param_values], ...}
        """
        self.value = value
        self.parameters = kw


class Component(object):
    """
    Parses and evaluates a component block.
        
        input :   string values for c_type and uid
                  a list of Property objects 
                  (Property objects can share the same name as a property
                  name can appear more than one time in a component)
        
        output :  unchanged c_type and uid
                  a dictionnary of versions of this component including
                  a dict {'property_name': PropertyValue[] } for properties
    """
    # XXX A parse method should be added to test properties inside of current 
    # component-type/properties (for example to test if property can appear
    # more than one time, ...)

    def __init__(self, c_type, uid):
        """
        Initialize the component.

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
        """
        Return the last version of current component or the sequence's one.
        """
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

        Note that it return values for the last version of this component.
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


    # To override a component proerty from the spec, or to add a new one,
    # define this class variable.
    schema = {
##        'DTSTART': DateTime(occurs=1, index='keyword'),
##        'DTEND': DateTime(occurs=1, index='keyword'),
    }


    @classmethod
    def get_datatype(cls, name):
        # Overriden schema
        if name in cls.schema:
            return cls.schema[name]
        # The specs schema
        if name in data_properties:
            return data_properties[name]
        # Default
        return String(occurs=0)


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


    #########################################################################
    # Load State
    #########################################################################
    def _load_state_from_file(self, file):
        # Initialize the data structures
        self._init_ical()

        # Read the data and figure out the encoding
        data = file.read()
        encoding = Text.guess_encoding(data)
        self.encoding = encoding

        # Parse
        lines = []
        for name, value, parameters in parse(data):
            # Deserialize
            datatype = self.get_datatype(name)
            if isinstance(datatype, Unicode):
                value = datatype.decode(value, encoding=encoding)
            else:
                value = datatype.decode(value)
            # Build the value (a PropertyValue instance)
            value = PropertyValue(value, **parameters)
            # Append
            lines.append((name, value))

        # Read first line
        first = lines[0]
        if (first[0] != 'BEGIN' or first[1].value != 'VCALENDAR'
            or len(first[1].parameters) != 0): 
            raise ValueError, 'icalendar must begin with BEGIN:VCALENDAR'

        lines = lines[1:]

        ###################################################################
        # Read properties
        n_line = 0
        for name, value in lines:
            if name == 'BEGIN':
                break
            elif name == 'END':
                break
            elif name == 'VERSION':
                if 'VERSION' in self.properties:
                    raise ValueError, 'VERSION can appear only one time'
            elif name == 'PRODID':
                if 'PRODID' in self.properties:
                    raise ValueError, 'PRODID can appear only one time'
            # Add the property
            self.properties[name] = value
            n_line += 1
        
        # The properties VERSION and PRODID are mandatory
        if 'VERSION' not in self.properties or 'PRODID' not in self.properties:
            raise ValueError, 'PRODID or VERSION parameter missing'

        lines = lines[n_line:]

        ###################################################################
        # Read components
        c_type = None
        uid = None
 
        for prop_name, prop_value in lines[:-1]:
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
                else:
                    datatype = self.get_datatype(prop_name)
                    if datatype.occurs == 1:
                        # Check the property has not yet being found
                        if prop_name in c_properties:
                            msg = ('the property %s can be assigned only one'
                                   ' value' % prop_name)
                            raise ValueError, msg
                        # Set the property
                        c_properties[prop_name] = prop_value
                    else:
                        value = c_properties.setdefault(prop_name, [])
                        value.append(prop_value)

        ###################################################################
        # Index components
        for uid in self.components:
            component = self.components[uid]
            self.catalog.index_document(component, uid)


    #########################################################################
    # Save State
    #########################################################################
    @classmethod
    def encode_property(cls, name, property_values, encoding='utf-8'):
        if not isinstance(property_values, list):
            property_values = [property_values]

        datatype = cls.get_datatype(name)

        lines = []
        for property_value in property_values:
            # The parameters
            parameters = ''
            for param_name in property_value.parameters:
                param_value = property_value.parameters[param_name]
                parameters += ';%s=%s' % (param_name, ','.join(param_value))

            # The value (encode)
            value = property_value.value
            if isinstance(datatype, Unicode):
                value = datatype.encode(value, encoding=encoding)
            else:
                value = datatype.encode(value)
            # The value (escape)
            value = value.replace("\\", "\\\\")
            value = value.replace("\r", "\\r").replace("\n", "\\n")

            # Build the line
            line = '%s%s:%s\n' % (name, parameters, value)
            if len(line) > 75:
                line = fold_line(line)

            # Append
            lines.append(line)

        return lines


    def to_str(self, encoding='UTF-8'):
        lines = []

        line = 'BEGIN:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        # Calendar properties
        for key in self.properties:
            value = self.properties[key]
            line = self.encode_property(key, value, encoding)
            lines.extend(line)
        # Calendar components
        for uid in self.components:
            component = self.components[uid]
            c_type = component.c_type
            for sequence in component.get_sequences():
                version = component.versions[sequence]
                # Begin
                line = 'BEGIN:%s\n' % c_type
                lines.append(Unicode.encode(line))
                # UID, SEQUENCE
                lines.append('UID:%s\n' % uid)
                lines.append('SEQUENCE:%s\n' % sequence)
                # Properties
                for key in version:
                    value = version[key]
                    line = self.encode_property(key, value, encoding)
                    lines.extend(line)
                # End
                line = 'END:%s\n' % c_type
                lines.append(Unicode.encode(line))

        line = 'END:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        return ''.join(lines)


    #######################################################################
    # To override
    #######################################################################
    def generate_uid(self, c_type):
        """ Generate a uid based on c_type and current datetime. """
        return ' '.join([c_type, datetime.now().isoformat()])


    #######################################################################
    # API
    #######################################################################
    def check_properties(self, properties):
        """
        Check each property has a correct number of occurrences.
        It replaces a unique value of a multiple occurrences allowed
        property by a list with this value.
        """
        for name, value in properties.items():
            datatype = self.get_datatype(name)
            if datatype.occurs == 1:
                if isinstance(value, list):
                    msg = 'property "%s" requires only one value' % name
                    raise TypeError, msg
            else:
                if not isinstance(value, list):
                    properties[name] = [value]

        return properties


    def add_component(self, c_type, **kw):
        """
        Add a new component of type c_type.
        It generates a uid and a new version with the given properties if any.
        """
        # Check the properties
        kw = self.check_properties(kw)

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
        """
        Update component with given uid with properties given as kw, 
        creating a new version based on the previous one.
        """
        # Check the properties
        kw = self.check_properties(kw)

        # Build the new version
        component = self.components[uid]
        version = component.get_version()
        version = version.copy()
        version.update(kw)
        # Remove deleted properties (value is None or [None])
        keys = []
        for key in version:
            if version[key] is None or version[key] == [None]:
                keys.append(key)
        for key in keys:
            del version[key]

        # Add the new version
        self.set_changed()
        component.add_version(version)

        # Index the component
        self.catalog.index_document(component, uid)


    def remove(self, uid):
        """
        Definitely remove from the calendar an existant component with all its
        versions. 
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
        Set values to the given calendar property, removing previous ones.

        name -- name of the property as a string
        values -- PropertyValue[]
        """
        datatype = self.get_datatype(name)
        if datatype.occurs == 1:
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
    def search_events(self, subset=None, **kw):
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

        It searches into all components or in the provided subset list of
        components.
        """
        res_events = []

        # Get the list of differents property names used to filter
        filters = kw.keys()

        # For each event
        events = subset or [self.components[x] 
                            for x in self.search(type='VEVENT')]
        for event in events:
            version = event.get_version()

            # For each filter
            for filter in filters:
                # If filter not in component, go to next one
                if filter not in version:
                    break
                # Test filter
                expected = kw.get(filter)
                property_value = version[filter]
                datatype = self.get_datatype(filter)
                if datatype.occurs == 1:
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


    def search_events_in_date(self, selected_date, sortby=None, **kw):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        date and sorted if requested.
        """
        dtstart = datetime(selected_date.year, selected_date.month,
                           selected_date.day)
        dtend = dtstart + timedelta(days=1) - resolution
        return self.search_events_in_range(dtstart, dtend, sortby=sortby, **kw)


    def search_events_in_range(self, dtstart, dtend, sortby=None, **kw):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        dates range and sorted  if requested.
        If kw is filled, it calls search_events on the found subset to return
        only components matching filters.
        """
        # Check type of dates, we need datetime for method in_range
        if not isinstance(dtstart, datetime):
            dtstart = datetime(dtstart.year, dtstart.month, dtstart.day)
        if not isinstance(dtend, datetime):
            dtend = datetime(dtend.year, dtend.month, dtend.day)
            # dtend is include into range
            dtend = dtend + timedelta(days=1) - resolution

        # Get only the events which matches
        query = And(Equal('type', 'VEVENT'),
                    Or(Range('dtstart', dtstart + resolution, dtend),
                       Range('dtend', dtstart + resolution, dtend),
                       And(Range('dtstart', None, dtstart + resolution),
                           Range('dtend', dtend, None))))
        results = [self.components[uid] for uid in self.search(query)]

        if results == []:
            return []

        # Check filters
        if kw:
            results = self.search_events(subset=results, **kw)

        # Nothing to sort or inactive
        if sortby is None or len(results) <= 1:
            return results

        # Get results as a dict to sort them
        res_events = []
        for event in results:
            version = event.get_version()
            value = {
                'dtstart': version['DTSTART'].value,
                'dtend': version['DTEND'].value,
                'event': event
              }
            res_events.append(value)
        # Sort by dtstart
        res_events = sorted(res_events, key=itemgetter('dtstart'))
        # Sort by dtend
        res = []
        current = [res_events[0]]
        for e in res_events[1:]:
            if e['dtstart'] == current[0]['dtstart']:
                current.append(e)
            else:
                res.extend(x['event'] 
                           for x in sorted(current, key=itemgetter('dtend')))
                current = [e]
        res.extend(x['event'] for x in sorted(current, 
                                              key=itemgetter('dtend')))
        return res


    # Test if any event corresponds to a given date
    def has_event_in_date(self, date):
        """
        Return True if there is at least one event matching the given date.
        """
        return self.search_events_in_date(date) != []


    def get_conflicts(self, date):
        """
        Returns a list of uid couples which happen at the same time.
        We check only last occurrence of events.
        """
        events = self.search_events_in_date(date)
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
                    atoms.append(Equal(key, value))

                query = And(*atoms)
            else:
                raise ValueError, "expected a query"

        documents = query.search(self)
        # Sort by weight
        documents = documents.keys()
        documents.sort()

        return documents

