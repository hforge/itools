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
from datetime import datetime, date, time
from copy import deepcopy
from operator import itemgetter
from time import time as get_time

# Import from itools
from itools.datatypes import Unicode, String
from itools.catalog import queries
from itools.handlers.Text import Text
from itools.csv.csv import Catalog
from itools.ical.types import PropertyType, ComponentType
from itools.ical.types import data_properties


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



class Parameter(object):

    def __init__(self, name, values):
        """
        Initialize the parameter.

        name -- name of the parameter as a string
        values -- list of values as strings
        """
        self.name, self.values = name, values


class Property(object):

    def __init__(self, name, property_value):
        """
        Initialize the property.

        name -- name of the property as a string
        property_value -- PropertyValue object or PropertyValue[]
        """
        occurs = PropertyType.nb_occurrences(name)
        if not isinstance(property_value, list) :
            property_value = [property_value, ]
        # If occurs == 1, then value is the first given value
        if occurs == 1:
            property_value = property_value[0]
        self.name, self.value = name, property_value



class PropertyValue(object):

    def __init__(self, value, parameters=None):
        """
        Initialize the property value.

        value -- value as a string
        parameters -- {param1_name: Parameter object, ...}
        """
        self.value, self.parameters = value, parameters
        if not self.parameters:
            self.parameters = {}


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
    # component-type/properties (for example to test if property can appear more
    # than one time, ...)

    def __init__ (self, c_type, properties=None, encoding='UTF-8'):
        """
        Initialize the component.

        properties -- {property1_name: Property object, ...}
        c_type -- type of component as a string (i.e. 'VEVENT')
        """
        self.c_type = c_type
        self.properties = properties
        if not properties:
            self.properties = {}
        self.encoding = encoding
        # We add arbitrarily an uid
        if 'UID' not in self.properties and 'uid' not in self.properties:
            self.add(Property('UID', PropertyValue(self.generate_uid())))
        # We add a sequence number equal to 0
        if 'SEQUENCE' not in self.properties and \
           'sequence' not in self.properties:
            self.add(Property('SEQUENCE', PropertyValue(0)))


    def generate_uid(self):
        return self.c_type +'-'+ datetime.now().strftime('%Y-%m-%d %H:%M:%S %p')
        
    #######################################################################
    # API
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

        # Properties
        if name not in self.properties:
            return None
        return self.properties[name].value


    # Get a property of current component
    def get_property_values(self, name=None):
        """
        Return the value of given name property as a PropertyValue or as a list
        of PropertyValue objects if it can occur more than once.

        Return icalendar property values as a dict {name: value, ...} where
        value is a PropertyValue or a list of PropertyValue objects if it can
        occur more than once.
        """
        if name:
            return self.properties.get(name, None)
        return self.properties


    def set_property(self, name, values):
        """
        Set values to the given property, removing previous ones.

        name -- name of the property as a string
        values -- PropertyValue or PropertyValue[]
        """
        occurs = PropertyType.nb_occurrences(name)
        if occurs != 1:
            if not isinstance(values, list):
                values = [values, ]
        else:
            if isinstance(values, list):
                if len(values) == 1:
                    values = values[0]
                else:
                    raise ValueError, 'property %s requires only one value'\
                                      % name
        self.properties[name] = values


    def add(self, property):
        """
        Add a property to current component.

        If this property can have several values, 
            append current to list.
        Else
            set it except if a value is already set for it.
        """
        if not isinstance(property, Property):
            raise 'ValueError', 'Add method take a Property object as parameter'

        # Build PropertyValue
        property_name, property_value = property.name, property.value

        # Get occurs
        occurs = 0
        if property_name in data_properties:
            occurs = data_properties[property_name].occurs

        # Set if several values allowed and at least already one set
        if occurs != 1:
            # property_value must be a list
            if not isinstance(property_value, list):
                property_value = [property_value, ]
            if property_name in self.properties:
                self.properties[property_name].extend(property_value)
                return
        # Set value (if not already set)
        if property_name not in self.properties:
            self.properties[property_name] = property_value
        else:
            raise 'ValueError', 'Property already set for current component, '\
                                'use set_property method.'


    # Test if a given date corresponds to current component
    def correspond_to_date(self, date):
        """
        Return False if date < 'DTSTART' or date > 'DTEND', 
        return True in all other cases
        """
        tuple_date = (date.year, date.month, date.day)

        # Get dates of current component
        dtstart, dtend, dtstamp = None, None, None
        if 'DTSTART' in self.properties:
            date = self.properties['DTSTART'].value
            tuple_dtstart = (date.year, date.month, date.day)
            if tuple_date < tuple_dtstart:
                return False
        if 'DTEND' in self.properties:
            date = self.properties['DTEND'].value
            tuple_dtend = (date.year, date.month, date.day)
            if tuple_date > tuple_dtend:
                return False
        return True 


    # Test if current event is in part of given range
    def in_range(self, start, end):
        """
        Return False if end < 'DTSTART' or start > 'DTEND', 
        return True in all other cases
        """
        tuple_start = (start.year, start.month, start.day, 
                       start.hour, start.minute, start.second)
        tuple_end = (end.year, end.month, end.day,
                     end.hour, end.minute, end.second)
        # If wrong order, we put it right
        if tuple_start > tuple_end:
            tmp = tuple_end
            tuple_end = tuple_start
            tuple_start = tmp

        # If end < DTSTART, then component happens earlier
        if 'DTSTART' in self.properties:
            dtstart = self.get_property_values('DTSTART')
            if isinstance(dtstart, list):
                dtstart = dtstart[0]
            dtstart = dtstart.value
            tuple_dtstart = (dtstart.year, dtstart.month, dtstart.day, 
                             dtstart.hour, dtstart.minute, dtstart.second)
            if tuple_end <= tuple_dtstart:
                return False
        # If start > DTEND, then component happens earlier
        if 'DTEND' in self.properties:
            dtend = self.get_property_values('DTEND')
            if isinstance(dtend, list):
                dtend = dtend[0]
            dtend, param = dtend.value, dtend.parameters
            tuple_dtend = (dtend.year, dtend.month, dtend.day, 
                           dtend.hour, dtend.minute, dtend.second)
            # If parameter 'VALUE' == 'DATE', event last all day
            if (dtend.hour + dtend.minute + dtend.second) == 0:
                param = param.get('VALUE', '')
                if param and 'DATE' in param.values:
                    tuple_dtend = (dtend.year, dtend.month, dtend.day, 
                                   23, 59, 59)
            if tuple_start >= tuple_dtend: 
                return False
        return True 



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
        self.components = []
        self.catalog = Catalog()
        self.catalog.add_index('type', 'keyword')
        self.catalog.add_index('uid', 'keyword')
        self.catalog.add_index('dtstart', 'keyword')
        self.catalog.add_index('dtend', 'keyword')


    def new(self):
        self._init_ical()

        properties = (
            ('VERSION', {}, u'2.0'), 
            ('PRODID', {}, u'-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN')
          )
        for name, param, value in properties:
            self.properties[name] = PropertyValue(value, param)

        # The encoding
        self.encoding = 'UTF-8'


    def _load_state_from_file(self, file):
        self._init_ical()

        data = None
        data = file.read()
        encoding = Text.guess_encoding(data)
        self.encoding = encoding

        value = []
        for line in unfold_lines(data):
            # Add tuple (name, PropertyValue) to list value keeping order
            prop = PropertyType.decode(line, encoding)
            value.append((prop.name, prop.value))

        status = 0
        nbproperties = 0
        optproperties = []

        if value[0][0]!='BEGIN' or value[0][1].value!='VCALENDAR' \
          or len(value[0][1].parameters)!=0 : 
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
        c_type = ''
 
        for prop_name, prop_value in value[nbproperties+1:-1]:
            if prop_name in ('PRODID', 'VERSION'):
                raise ValueError, 'PRODID and VERSION must appear before '\
                                  'any component'
            if c_type == '':
                if prop_name == 'BEGIN':
                    c_type = prop_value.value
                    component = ()
                continue

            if prop_name == 'END':
                if prop_value.value == c_type:
                    comp = ComponentType.decode(component, c_type, encoding)
                    self.add_component(comp)
                    c_type = ''
                #elif prop_value.value in component_list:
                #    raise ValueError, '%s component can NOT be inserted '\
                #          'into %s component' % (prop_value.value, c_type)
                else:
                    raise ValueError, 'Inner components are not managed yet'
            else:
                component = component + ((prop_name, prop_value,),)

        if len(self.components) == 0:
            print 'WARNING : '\
                  'an icalendar file should contain at least ONE component'


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
        for component in self.components:
            if component is not None:
                lines.append(ComponentType.encode(component))

        line = 'END:VCALENDAR\n'
        lines.append(Unicode.encode(line))

        return ''.join(lines)


    #######################################################################
    # API
    #######################################################################
    def add_component(self, component):
        # The (internal) component id
        n = len(self.components)
        # Add the component
        self.components.append(component)
        # Index the component
        self.catalog.index_document(component, n)


    def add(self, element):
        """
        Add an element to the current icalendar object.

        element -- Component/Property object
        """
        if isinstance(element, Component):
            self.add_component(element)
        elif isinstance(element, Property):
            name = element.name
            if not name in self.properties:
                self.properties[name] = element.value
        else:
            raise ValueError, ('Only Property and Component object types can'
                               ' be added to an icalendar object.')


    def remove(self, type, uid):
        """
        Definitely remove from the calendar each occurrence of an existant
        component. 
        """
        self.set_changed()
        for n in self.search(uid=uid):
            component = self.components[n]
            self.components[n] = None
            # Unindex
            self.catalog.unindex_document(component, n)


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
        # Get a list if it is not.
        if not isinstance(values, list):
            values = [values, ]
        # If the property can occur only once, set the first value of the
        # list, ignoring others
        occurs = PropertyType.nb_occurrences(name)
        if occurs == 1:
            values = values[0]
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


    def duplicate_component(self, component):
        new = deepcopy(component)
        seq = new.get_property_values('SEQUENCE')
        if not seq:
            component.set_property('SEQUENCE', PropertyValue(0))
            seq = PropertyValue(0)
        seq = seq.value + 1
        new.set_property('SEQUENCE', PropertyValue(seq))
        return new


    def is_last(self, component):
        """
        Return True if current component has the biggest sequence number (or
        none) of all components with its UID
        """
        sequence = component.get_property_values('SEQUENCE')
        if not sequence:
            return True
        uid = component.get_property_values('UID').value
        components = self.get_component_by_uid(uid, False)
        return sequence.value == (len(components) - 1)

 
    # Get some events corresponding to arguments
    def search_events(self, only_last=True, **kw):
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
            if only_last and not self.is_last(event):
                continue
            add_to_res = False
            # For each filter
            for filter in filters:
                # If filter not in component, go to next one
                if filter not in event.properties:
                    add_to_res = False
                    break
                # Test filter
                expected = kw.get(filter)
                property_value = event.properties[filter]
                occurs = PropertyType.nb_occurrences(filter) 
                if occurs == 1:
                    if property_value.value != expected:
                        add_to_res = False
                        break
                    add_to_res = True
                else:
                    add_to_res = False
                    for item in property_value:
                        if isinstance(expected, list):
                            if item.value in expected:
                                add_to_res = True
                                break
                        elif item.value == expected:
                            add_to_res = True
                            break
                # If filter do not match component, go to next one
                if not add_to_res:
                    break
            else:
                add_to_res = True

            # Add event if all filters match
            if add_to_res:
                res_events.append(event)

        return res_events


    def get_component_by_uid(self, uid, only_last=True):
        """
        Return components with the given uid, None if it doesn't appear.
        If only_last is True, return only the last occurrence.
        """
        components = self.search_events(only_last, UID='%s' %uid)
        if not only_last and components:
            return components
        for component in components:
            if self.is_last(component):
                return component
        return None


    # Get some events corresponding to a given date
    def get_events_in_date(self, date, only_last=True):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        date. 
        If only_last is True, return only the last occurrences.
        """
        res_events = []

        # Get only the events which matches
        for event in self.get_components('VEVENT'):
            if event.correspond_to_date(date):
                if not only_last or self.is_last(event):
                    res_events.append(event)

        return res_events


    def get_events_in_range(self, dtstart, dtend, only_last=True):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        dates range. 
        The only_last True value means only getting events with last sequence
        number (history).
        """
        res_events = []

        # Get only the events which matches
        for event in self.get_components('VEVENT'):
            if only_last and not self.is_last(event):
                continue
            if event.in_range(dtstart, dtend):
                res_events.append(event)

        return res_events


    def get_sorted_events_in_date(self, selected_date, only_last=True):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        date and sorted chronologically.
        The only_last True value means only getting events with last sequence
        number (history).
        """
        dtstart = datetime.combine(selected_date, time(0,0))
        dtend = datetime.combine(selected_date, time(23,59))

        return self.get_sorted_events_in_range(dtstart, dtend, only_last)


    def get_sorted_events_in_range(self, dtstart, dtend, only_last=True):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        dates range and sorted chronologically.
        The only_last True value means only getting events with last sequence
        number (history).
        """
        res_events = []

        # Check type of dates, we need datetime for method in_range
        if not isinstance(dtstart, datetime):
            dtstart = datetime(dtstart.year, dtstart.month, dtstart.day)
        if not isinstance(dtend, datetime):
            dtend = datetime(dtend.year, dtend.month, dtend.day)

        # Get only the events which matches
        t0 = get_time()
        for n in self.search(type='VEVENT'):
            event = self.components[n]
            if only_last and not self.is_last(event):
                continue
            if event.in_range(dtstart, dtend):
                value = {
                    'dtstart': event.get_property_values('DTSTART').value,
                    'dtend': event.get_property_values('DTEND').value,
                    'event': event
                  }
                res_events.append(value)
        t1 = get_time()
        print t1-t0
        
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
            dtstart_ref = event_ref.get_property_values('DTSTART').value
            dtend_ref = event_ref.get_property_values('DTEND').value
            # For each other event, we test if there is a conflict
            for j, event in enumerate(events):
                if j <= i:
                    continue
                dtstart = event.get_property_values('DTSTART').value
                dtend = event.get_property_values('DTEND').value

                if dtstart >=  dtend_ref or dtend <= dtstart_ref:
                    continue
                conflicts.append((i, j))

        # Replace index of components by their UID
        if conflicts != []:
            for index, (i, j) in enumerate(conflicts):
                i = events[i].get_property_values('UID').value
                j = events[j].get_property_values('UID').value
                conflicts[index] = (i, j)

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

