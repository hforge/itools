# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Deram <nderam@gmail.com>  
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
from datetime import datetime

# Import from itools
from itools.datatypes.base import DataType
from itools.datatypes import Integer, URI, Unicode, String


def fold_line(line):
    """
    Fold the unfolded line over 75 characters.
    """
    i = 1
    lines = line.split(' ')
    res = lines[0] 
    size = len(res)
    while i < len(lines):
        # Still less than 75c
        if size+len(lines[i]) <= 75:
            res = res + ' ' + lines[i] 
            size = size + 1 + len(lines[i]) 
            i = i + 1
        # More than 75c, insert new line
        else:
            res = res + '\n ' + lines[i]
            size = len(lines[i]) 
            i = i + 1
    return res



class DateTime(DataType):

    @staticmethod
    def decode(value):
        if value is None:
            return None

        year, month, day, hour, min, sec= 0, 0, 0, 0, 0, 0
        date = value[:8]
        year, month, day = int(date[:4]), int(date[4:6]), int(date[6:8])

        """
        Different formats for date-time :

            DTSTART:19970714T133000            ;Local time
            DTSTART:19970714T173000Z           ;UTC time
            DTSTART;TZID=US-Eastern:19970714T133000  ;Local time and time
                                                     ; zone reference

        Time can contain a micro-second value but it is facultative.
        """

        # Time can be omitted 
        if 'T' in value:
            time = value[9:]

            # ignore final Z for now
            if time[-1] == 'Z':
                time = time[:-1]
            else:
                pass
                # a parameter can have be added with utc info
                # ...

            hour, min = int(time[:2]), int(time[2:4])
            if len(time) == 6:
                sec = int(time[4:6])

        return datetime(year, month, day, hour, min, sec)


    @staticmethod
    def encode(value):
    # PROBLEM --> 2 formats, with or without final 'Z' 
        if value is None:
            return ''

        dt = value.isoformat('T')
        dt = dt.replace(':','')
        dt = dt.replace('-','')

        return dt   


    @staticmethod
    def from_str(value):
        if not value:
            return None
        date, time = value, None
        if ' ' in value:
            date, time = value.split()
        # Date
        year, month, day = date.split('-')
        year, month, day = int(year), int(month), int(day)
        # If no time
        if not time:
             return datetime(year, month, day)
        # Time
        if time.count(':') == 1:
            hours, minutes = time.split(':')
            hours, minutes, seconds = int(hours), int(minutes), 0
        else:
            hours, minutes, seconds = time.split(':')
            hours, minutes, seconds = int(hours), int(minutes), int(seconds)
        return datetime(year, month, day, hours, minutes, seconds)


    @staticmethod
    def to_str(value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')



# Tokens
TPARAM, TVALUE = range(2)
token_name = ['name', 'parameter', 'value']

# data types for each property
# --> TO VERIFY AND COMPLETE
# occurs = 0  means 0..n occurrences
data_properties = {
  'BEGIN': Unicode(occurs=1), 
  'END': Unicode(occurs=1), 
  'VERSION': Unicode(occurs=1), 
  'PRODID': Unicode(occurs=1), 
  'METHOD': Unicode(occurs=1), 
  # Component properties
  'ATTACH': URI(occurs=0), 
  'CATEGORY': Unicode(occurs=1), 
  'CATEGORIES': Unicode(occurs=0), 
  'CLASS': Unicode(occurs=1), 
  'COMMENT': Unicode(occurs=0), 
  'DESCRIPTION': Unicode(occurs=1), 
  'GEO': Unicode(occurs=1), 
  'LOCATION': Unicode(occurs=1), 
  'PERCENT-COMPLETE': Integer(occurs=1), 
  'PRIORITY': Integer(occurs=1), 
  'RESOURCES': Unicode(occurs=0), 
  'STATUS': Unicode(occurs=1), 
  'SUMMARY': Unicode(occurs=1), 
  # Date & Time component properties
  'COMPLETED': DateTime(occurs=1), 
  'DTEND': DateTime(occurs=1), 
  'DUE': DateTime(occurs=1), 
  'DTSTART': DateTime(occurs=1), 
  'DURATION': Unicode(occurs=1), 
  'FREEBUSY': Unicode(occurs=1), 
  'TRANSP': Unicode(occurs=1), 
  # Time Zone component properties
  'TZID': Unicode(occurs=1), 
  'TZNAME': Unicode(occurs=0), 
  'TZOFFSETFROM': Unicode(occurs=1), 
  'TZOFFSETTO': Unicode(occurs=1), 
  'TZURL': URI(occurs=1),
  # Relationship component properties
  'ATTENDEE': URI(occurs=0),
  'CONTACT': Unicode(occurs=0),
  'ORGANIZER': URI(occurs=1), 
  # Recurrence component properties
  'EXDATE': DateTime(occurs=0), 
  'EXRULE': Unicode(occurs=0), 
  'RDATE': Unicode(occurs=0), 
  'RRULE': Unicode(occurs=0), 
  # Alarm component properties
  'ACTION': Unicode(occurs=1), 
  'REPEAT': Integer(occurs=1), 
  'TRIGGER': Unicode(occurs=1), 
  # Change management component properties
  'CREATED': DateTime(occurs=1), 
  'DTSTAMP': DateTime(occurs=1), 
  'LAST-MODIFIED': DateTime(occurs=1), 
  'SEQUENCE': Integer(occurs=1), 
  # Others
  'RECURRENCE-ID': DateTime(occurs=1), 
  'RELATED-TO': Unicode(occurs=1), 
  'URL': URI(occurs=1), 
  'UID': Unicode(occurs=1)
}

################################################################
#                         NOT USED ACTUALLY  
#statvalue = {'VEVENT': ['TENTATIVE', 'CONFIRMED', 'CANCELLED']}
#classvalue = ['PRIVATE', 'PUBLIC', 'CONFIDENTIAL']
################################################################

class PropertyType(object):
    """
    Manage an icalendar content line property :
    
      name *(;param-name=param-value1[, param-value2, ...]) : value CRLF
      
    """
    ###################################################################
    # Parse the property line separating as :  
    #
    #   property name  >  name
    #   value & parameter list > property_value 
    # 
    #   XXX test if the property accepts the given parameters 
    #       could be a great idea but could be done on Component
    # 
    ###################################################################
    @classmethod
    def parse(cls, property, encoding='UTF-8'):
        """
        Parse content line property splitting it into 2 parts:
            name | [parameters]value
        """
        c, lexeme = property[0], ''
        # Test first character of name
        if not c.isalnum() and c != '-':
            raise SyntaxError, 'unexpected character (%s)' % c
        # Test if property contains ':'
        if not ':' in property:
            raise SyntaxError, 'character (:) must appear at least one time'
        # Cut name
        while not c in (';', ':'):
            property = property[1:]
            if c.isalnum() or c == '-':
                lexeme += c
            else:
                raise SyntaxError, "unexpected character '%s' (%s)" % (c, ord(c))
            c = property[0]

        return lexeme, property


    @classmethod
    def decode(cls, line, encoding='UTF-8'):
        # XXX get only one property line instead of all of this name and so
        # multiple lines in input
        name, value, parameters = None, None, {}
        # Get name
        name, value = PropertyType.parse(line, encoding)
        # Get PropertyValue (parameters and value)
        value = PropertyValueType.decode(name, value, encoding)
        from itools.ical.icalendar import Property
        return Property(name, value)


    @classmethod
    def encode(cls, name, property):
        lines = ''
        # If we get a PropertyValue, we recreate a whole Property
        from itools.ical.icalendar import Property, PropertyValue
        if isinstance(property, PropertyValue):
            property = Property(name, property)
        # Property name
        name = property.name
        property_values = property.value
        # For each property_value
        if isinstance(property_values, list):
            for property_value in property_values:
                current = name + PropertyValueType.encode(name, property_value)
                lines = lines + current + '\n'
        else:
            current = name + PropertyValueType.encode(name, property_values)
            lines = current + '\n'
        return lines


    # Get number of occurrences for given property name
    @classmethod
    def nb_occurrences(cls, name):
        if name in data_properties:
            return data_properties[name].occurs
        return 0



class PropertyValueType(object):
    """
    Manage an icalendar content line value property [with parameters] :
    
      *(;param-name=param-value1[, param-value2, ...]) : value CRLF
      
    """

    ###################################################################
    # Lexical & syntaxic analysis
    #   status :
    #     1 --> parameter begun (just after ';')
    #     2 --> param-name begun 
    #     3 --> param-name ended, param-value beginning
    #     4 --> param-value quoted begun (just after '"')
    #     5 --> param-value NOT quoted begun 
    #     6 --> param-value ended (just after '"' for quoted ones)
    #     7 --> value to begin (just after ':')
    #     8 --> value begun 
    ###################################################################
    @classmethod
    def get_tokens(cls, property):
        status, lexeme, last = 0, '', ''

        # Init status
        c, property = property[0], property[1:]
        if c == ';':
            status = 1
        elif c == ':':
            status = 7
            
        for c in property:
            # parameter begun (just after ';')
            if status == 1:
                if c.isalnum() or c in ('-'):
                    lexeme, status = c, 2
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)

            # param-name begun 
            elif status == 2:
                if c.isalnum() or c in ('-'):
                    lexeme += c
                elif c == '=':
                    lexeme += c
                    status = 3
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)

            # param-name ended, param-value beginning
            elif status == 3:
                if c == '"':
                    lexeme += c
                    status = 4
                elif c in (';',':',',') :
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                else:    
                    lexeme += c
                    status = 5

            # param-value quoted begun (just after '"')
            elif status == 4:
                if c == '"':
                    lexeme += c
                    status = 6
                else:
                    lexeme += c

            # param-value NOT quoted begun 
            elif status == 5:
                if c in (':',';',',') :
                    status = 6
                elif c=='"':
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                else:    
                    lexeme += c

            # value to begin (just after ':')
            elif status == 7:
                lexeme, status = c, 8

            # value begun 
            elif status == 8:
                lexeme += c

            # param-value ended (just after '"' for quoted ones)
            if status == 6:
                if c == ':':
                    status = 7
                    yield TPARAM, lexeme
                elif c == ';': 
                    status = 1
                    yield TPARAM, lexeme
                elif c == ',': 
                    lexeme += c
                    status = 3
                elif c == '"':
                    if last == '"':
                        raise SyntaxError, 'unexpected repeated character (%s)'\
                              ' at status %s' % (c, status)
                    last = '"'
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)

        if status not in (7, 8):
            raise SyntaxError, 'unexpected property (%s)' % property

        yield TVALUE, lexeme


    ###################################################################
    # Parse parameters and value                                      #
    ###################################################################
    @classmethod
    def parse(cls, name, property, encoding='UTF-8'):
        """
        Parse content line property parameters and value.
        """
        value, parameters = None, {}

        for token, lexeme in PropertyValueType.get_tokens(property):
            if token == TPARAM:
                param_name, param_value = lexeme.split('=')
                parameters[param_name] = ParameterType.decode(lexeme)
            elif token == TVALUE:
                #####################################
                # Change types of values when needed
                vtype = data_properties.get(name, String)
                if isinstance(vtype, Unicode):
                    value = vtype.decode(lexeme, encoding)
                else:
                    value = vtype.decode(lexeme)
            else:
                raise SyntaxError, 'unexpected %s' % token_name[token]

        return value, parameters


    @classmethod
    def encode(cls, name, property_value):
        lines = ''
        # Property parameters
        if property_value.parameters:
            for key_param in property_value.parameters:
                lines = lines + ';' + \
                   ParameterType.encode(property_value.parameters[key_param])

        # property_value value
        vtype = data_properties.get(name, String)
        value = vtype.encode(property_value.value)
        value = value.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")
        lines = lines + ':' + value
        # property_value folded if necessary
        if len(lines) > 75:
            lines = fold_line(lines)
        return lines


    @classmethod
    def decode(cls, name, string, encoding='UTF-8'):
        value, parameters = None, {}
        # Parsing
        value, parameters = PropertyValueType.parse(name, string, encoding)
        if isinstance(value, unicode):
            tokens = []
            for token in value.split(u'\\\\'):
                token = token.replace(u"\\r", u"\r").replace(u"\\n", u"\n")
                tokens.append(token)
            value = u'\\'.join(tokens)
        from itools.ical.icalendar import PropertyValue
        return PropertyValue(value, parameters)



class ParameterType(object):
    """
    Manage an icalendar parameter :
    
      ;param-name=param-value1[, param-value2, ...]
      
    """

    ###################################################################
    # Semantic analysis. 
    #
    #   XXX test if the parameter accepts the given values
    #       could be a great idea
    # 
    #   property name  >  name
    #   values list    >  values
    # 
    ###################################################################
    @classmethod
    def parse(cls, parameter, encoding='UTF-8'):
        name, values = None, []
        name, values_str = parameter.split('=')
        values = values_str.split(',')
        return name, values


    @classmethod
    def decode(cls, parameter, encoding='UTF-8'):
        name, values = None, []

        # Parsing (omitting first character ';')
        name, values = ParameterType.parse(parameter, encoding)

        from itools.ical.icalendar import Parameter
        return Parameter(name, values)


    @classmethod
    def encode(cls, parameter):
        # Parameter name
        param = str(parameter.name) + '='
        # Parameter values
        param = param + str(parameter.values[0])
        for value in parameter.values[1:]:
            param = param + ',' + str(value)
        return param



class ComponentType(object):
    """
    Manage an icalendar component :
    
      BEGIN:componentName
      
        ... properties ...

      END:componentName
    """

    ###################################################################
    # Semantic analysis. 
    #
    #   - Regroup values of the same property into a list when allowed
    # 
    #   XXX test if number of occurrences of properties is correct
    # 
    ###################################################################
    @classmethod
    def parse(cls, properties, c_type, encoding='UTF-8'):
        props = {}

        for prop_name, prop_value in properties:
            occurs = PropertyType.nb_occurrences(prop_name)
            # If always found
            if prop_name in props:
                if occurs == 1:
                    raise SyntaxError, 'Property %s can be assigned only one '\
                                       'value' % prop_name
                props[prop_name].extend(prop_value)
            #elif occurs == 1:
            #    props[prop_name] = prop_value
            else:
                props[prop_name] = prop_value

        return props


    @classmethod
    def decode(cls, properties, c_type, encoding='UTF-8'):
        props = {}

        # Parsing
        props = ComponentType.parse(properties, c_type, encoding)

        from itools.ical.icalendar import Component
        return Component(c_type, props)


    @classmethod
    def encode(cls, component):
        lines = []

        line = 'BEGIN:%s\n' % component.c_type
        lines.append(Unicode.encode(line))

        for key in component.properties:
            occurs = PropertyType.nb_occurrences(key)
            if occurs == 1:
                line = PropertyType.encode(key, component.properties[key])
                lines.append(line)
            else:
                for item in component.properties[key]:
                    lines.append(PropertyType.encode(key, item))

        line = 'END:%s\n' % component.c_type
        lines.append(Unicode.encode(line))

        return ''.join(lines)

