# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas Deram <nderam@gmail.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from Python Standard Library
from pprint import pprint
from datetime import datetime

# Import from itools
from itools.handlers.Text import Text
from itools.datatypes import Unicode, String
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

    def __init__(self, value, parameters={}):
        """
        Initialize the property value.

        value -- value as a string
        parameters -- {param1_name: Parameter object, ...}
        """
        self.value, self.parameters = value, parameters


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

    def __init__ (self, c_type, properties={}, encoding='UTF-8'):
        """
        Initialize the component.

        properties -- {property1_name: Property object, ...}
        c_type -- type of component as a string (i.e. 'VEVENT')
        """
        self.c_type = c_type
        self.properties = properties
        self.encoding = encoding
        # We add arbitrarily an uid
        if 'UID' not in properties and 'uid' not in properties:
            self.add(Property('UID', PropertyValue(self.generate_uid())))


    def generate_uid(self):
        return self.c_type +'-'+ datetime.now().strftime('%Y-%m-%d %H:%M:%S %p')
        
    #######################################################################
    # API
    #######################################################################

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
            if tuple_end < tuple_dtstart:
                return False
        # If start > DTEND, then component happens earlier
        if 'DTEND' in self.properties:
            dtend = self.get_property_values('DTEND')
            if isinstance(dtend, list):
                dtend = dtend[0]
            dtend = dtend.value
            tuple_dtend = (dtend.year, dtend.month, dtend.day, 
                           dtend.hour, dtend.minute, dtend.second)
            if tuple_start > tuple_dtend: 
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

    class_mimetypes = ['text/calendar']
    class_extension = 'ics'


    #########################################################################
    # The skeleton
    #########################################################################
    @classmethod
    def get_skeleton(cls):
        skel = (
            'BEGIN:VCALENDAR\n'
            'VERSION:2.0\n'
            'PRODID:-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN\n'
            'END:VCALENDAR\n')

        return skel


    def _load_state(self, resource):
        """ """
        self.properties = {}
        self.components = {}

        data = None
        data = resource.read()
        self.encoding = Text.guess_encoding(data)

        value = []
        for line in unfold_lines(data):
            # Add tuple (name, PropertyValue) to list value keeping order
            prop = PropertyType.decode(line, self.encoding)
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
            print done
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
            else:
                if prop_name == 'END':
                    if prop_value.value == c_type:
                        comp = ComponentType.decode(component, c_type,
                                                    self.encoding)
                        # Initialize state for current type if don't exist yet
                        if not c_type in self.components:
                            self.components[c_type] = []
                        self.components[c_type].append(comp)
                        c_type = ''
                    #elif prop_value.value in component_list:
                    #    raise ValueError, '%s component can NOT be inserted '\
                    #          'into %s component' % (prop_value.value, c_type)
                    else:
                        raise ValueError, 'Inner components are not managed yet'
                else:
                    component = component + ((prop_name, prop_value,),)

        if self.components == {}:
            print 'WARNING : '\
                  'an icalendar file should contain at least ONE component'
            #raise ValueError, 'an icalendar file must contain '\
            #                  'at least ONE component'


    def to_str(self, encoding='UTF-8'):
        """ """
        lines = []

        lines.append('BEGIN:VCALENDAR\n')
        # Calendar properties
        for key in self.properties:
            occurs = PropertyType.nb_occurrences(key) 
            if occurs == 1:
                lines.append(PropertyType.encode(key, self.properties[key]))
            else:
                for property_value in self.properties[key]:
                    lines.append(PropertyType.encode(key, property_value))
        # Calendar components
        for type_component in self.components:
            for component in self.components[type_component]:
                lines.append(ComponentType.encode(component))

        lines.append('END:VCALENDAR\n')

        return ''.join(lines)


    #######################################################################
    # API
    #######################################################################

    def add(self, element):
        """
        Add an element to the current icalendar object.

        element -- Component/Property object
        """
        if isinstance(element, Component):
            c_type = element.c_type
            if not c_type in self.components:
                self.components[c_type] = []
            self.components[c_type].append(element)
        elif isinstance(element, Property):
            name = element.name
            if not name in self.properties:
                self.properties[name] = element.value
        else:
            raise ValueError, 'Only Property and Component object types can be'\
                              ' added to an icalendar object.'


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
        # If the property can occur only once, set the first value of the list,
        # ignoring others
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

        components = []
        if type in self.components:
            components = self.components[type]
        if type == 'others':
            for key in self.components:
                if key not in ('VEVENT', 'VTODO', 'VJOURNAL', 'VFREEBUSY',
                               'VTIMEZONE'):
                    components.append(self.components[key])
        return components


    # Get some events corresponding to arguments
    def search_events(self, **kw):
        """
        Return a list of Component objects of type 'VEVENT' corresponding to the
        given filters.
        It should be used like this, for example:

            events = cal.search_events(
                STATUS='TENTATIVE', 
                PRIORITY=1,
                ATTENDEE=[URI.decode('MAILTO:jdoe@itaapy.com'),
                          URI.decode('MAILTO:jsmith@itaapy.com')])

        ** With a list of values, events match if at least one value matches
        """
        res_events, res_event = [], None

        # Get the list of differents property names used to filter
        filters = kw.keys()

        # If no event
        if 'VEVENT' not in self.components:
            return []

        # For each events
        for event in self.components['VEVENT']:
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

            # Add event if all filters match
            if add_to_res:
                res_events.append(event)

        return res_events


    def get_component_by_uid(self, uid):
        """
        Return a Component object with the given uid, None if it doesn't appear.
        """
        components = self.search_events(UID='%s' %uid)
        if components:
            return components[0]
        return None


    # Get some events corresponding to a given date
    def get_events_in_date(self, date):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        date.  """
        res_events, res_event = [], None

        if 'VEVENT' not in self.components:
            return []

        # Get only the events which matches
        for event in self.components['VEVENT']:
            if event.correspond_to_date(date):
                res_events.append(event)

        return res_events


    # Get some events corresponding to a given dates range
    def get_events_in_range(self, dtstart, dtend):
        """
        Return a list of Component objects of type 'VEVENT' matching the given
        dates range.  """
        res_events, res_event = [], None

        if 'VEVENT' not in self.components:
            return []

        # Get only the events which matches
        for event in self.components['VEVENT']:
            if event.in_range(dtstart, dtend):
                res_events.append(event)

        return res_events


    # Test if any event corresponds to a given date
    def has_event_in_date(self, date):
        """
        Return True if there is at least one event matching the given date.
        """
        return self.get_events_in_date(date) != []


    def get_conflicts(self, date):
        """
        Returns a list of uid couples which happen at the same time.
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

                if dtstart >  dtend_ref or dtend <= dtstart_ref:
                    continue
                conflicts.append((i, j))

        # Replace index of components by their UID
        if conflicts != []:
            for index, (i, j) in enumerate(conflicts):
                i = events[i].get_property_values('UID').value
                j = events[j].get_property_values('UID').value
                conflicts[index] = (i, j)

        return conflicts

