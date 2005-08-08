# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas Deram <nderam@gmail.com> & 
#                    Nicolas Oyez <nicoyez@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from Python Standard Library
from pprint import pprint

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
        self.name, self.values = name, values


class Property(object):

    def __init__(self, name, value, parameters={}):
        self.name, self.value, self.parameters = name, value, parameters


class PropertyValue(object):

    def __init__(self, value, parameters={}):
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

    def __init__ (self, properties, c_type, encoding='UTF-8'):
        self.properties = properties
        self.c_type = c_type
        self.encoding = encoding

    #######################################################################
    # API
    #######################################################################

    # Get a property of current component
    def get_property_values(self, name):
        return self.properties.get(name, None)


    # Set a property of current component
    # The property can hold more than one value.
    # So we change all values for the property name.
    # The list "values" must contain couples (value, parameters={})
    def set_property(self, name, values):
        occurs = PropertyType.nb_occurrences(name)
        if occurs == 1:
            value, parameters = values
            self.properties[name] = PropertyValue(value, parameters)
        else:
            prop_values = []
            for value, parameters in values:
                prop_values.append(PropertyValue(value, parameters))
            self.properties[name] = prop_values


    # Add a property to current component
    # but do nothing if property is already used and can be used only one time
    def add(self, name, value, parameters={}):
        prop = PropertyValue(value, parameters)

        if name in self.properties:
            occurs = 0
            if name in data_properties:
                occurs = data_properties[name].occurs
            if occurs == 1:
                print 'SyntaxError', 'This property can appear only one time.'
                return
        else:
            self.properties[name] = []
        self.properties[name].append(prop)



    # Test if a given date corresponds to current component
    def correspond_to_date(self, date):
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
    def get_skeleton(self):

        skel = (
            'BEGIN:VCALENDAR\n'
            'VERSION\n'
            ' :2.0\n'
            'PRODID\n'
            ' :-//itaapy.com/NONSGML ikaaro icalendar V1.0//EN\n'
            'END:VCALENDAR\n')

        return skel


    def _load_state(self, resource):
        state = self.state

        state.properties = {}
        state.components = {}

        data = None
        data = resource.read()
        state.encoding = Text.guess_encoding(data)

        value = []
        for line in unfold_lines(data):
            # Add tuple (name, PropertyValue) to list value keeping order
            prop_name, prop_value = PropertyType.decode(line, state.encoding)
            value.append((prop_name, prop_value))

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
            state.properties[prop_name] = prop_value

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
                        comp = ComponentType.decode(component, c_type, \
                                                    self.state.encoding)
                        # Initialize state for current type if don't exist yet
                        if not c_type in state.components:
                            state.components[c_type] = []
                        state.components[c_type].append(comp)
                        c_type = ''
                    elif prop_value.value in component_list:
                        raise ValueError, '%s component can NOT be inserted '\
                              'into %s component' % (prop_value.value, c_type)
                else:
                    component = component + ((prop_name, prop_value,),)

        if state.components == {}:
            print 'WARNING : '\
                  'an icalendar file should contain at least ONE component'
            #raise ValueError, 'an icalendar file must contain '\
            #                  'at least ONE component'


    def to_unicode(self, encoding='UTF-8'):
        lines = []

        lines.append(u'BEGIN:VCALENDAR')
        # Calendar properties
        for key in self.state.properties:
            lines.append(PropertyType.to_unicode(key, 
                                                 self.state.properties[key]))
        # Calendar components
        for type_component in self.state.components:
            for component in self.state.components[type_component]:
                lines.append(ComponentType.to_unicode(component))

        lines.append(u'END:VCALENDAR\n')

        return u'\n'.join(lines)


    #######################################################################
    # Get methods
    #######################################################################
    def get_properties(self):
        return self.state.properties
    properties = property(get_properties, None, None, '')


    def get_components_of(self, type):
        components = []
        if type in self.state.components:
            components = self.state.components[type]
        if type == 'others':
            for key in self.state.components:
                if key not in ('VEVENT', 'VTODO', 'VJOURNAL', 'VFREEBUSY',
                               'VTIMEZONE'):
                    components.append(self.state.components[key])
        return components


    #######################################################################
    # API
    #######################################################################

    # Get a calendar property
    def get_property_values(self, name):
        return self.properties.get(name, None)

    # Get some events corresponding to arguments
    def get_events_filtered(self, **kw):
        res_events, res_event = [], None

        # Get the list of differents property names used to filter
        filters = kw.keys()

        # Get only the events which matches
        if not self.state.components['VEVENT']:
            return []
        for event in self.state.components['VEVENT']:
            next_event = False

            for filter in filters:
                values = kw.get(filter)

                next_event = True

                occurs = PropertyType.nb_occurrences(filter) 
                if occurs == 1:
                    if event.properties[filter].value in values:
                        next_event = False
                        break
                else:                        
                    for item in event.properties[filter]:
                        if item.value in values:
                            next_event = False
                            break

#            for property in event.properties:
#                if next_event:
#                    break
#                for filter in filters:
#                    values = kw.get(filter)
#                    # Test is large because of multiple values
#                    if property.name == filter:
#                        next_event = True
#                        for item in property.values:
#                            if item in values:
#                                next_event = False
#                                break

            if not next_event:
                res_events.append(event)

        return res_events


    def get_component_by_uid(self, uid):
        components = self.get_events_filtered(UID='%s' %uid)
        if components:
            return components[0]
        return None


    # Get some events corresponding to a given date
    def get_events_by_date(self, date):
        res_events, res_event = [], None

        if 'VEVENT' not in self.state.components:
            return []

        # Get only the events which matches
        for event in self.state.components['VEVENT']:
            if event.correspond_to_date(date):
                res_events.append(event)

        return res_events


    def add_component(self, component, c_type):
        self.state.components[c_type].append(component)

