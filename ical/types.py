# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas Deram <nderam@gmail.com>  
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
from datetime import datetime
from string import atoi, replace

# Import from itools
from itools.types import Integer, URI, Unicode, String


def fold_line(line):
    """
    Fold the unfolded line over 75 characters.
    """
    i = 1
    lines = line.split(' ')
    res = lines[0] 
    size = len(res)
    while i < len(lines):
        if size+len(lines[i]) <= 75:
            res = res + ' ' + lines[i] 
            size = size + 1 + len(lines[i]) 
            i = i + 1
        else:
            res = res + ' \n '
            res = res + lines[i]
            size = len(lines[i]) 
            i = i + 1
    return res



class DateTime(object):

    def decode(cls, value):
        if value is None:
            return None
            
        year, month, day, hour, min, sec= 0, 0, 0, 0, 0, 0
        date = value[:8]
        year, month, day = atoi(date[:4]), atoi(date[4:6]), atoi(date[6:8])
        
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
            
            hour, min = atoi(time[:2]), atoi(time[2:4])
            if len(time) == 6:
                sec = atoi(time[4:6])
            
        return datetime(year, month, day, hour, min, sec)

    decode = classmethod(decode)


    def encode(cls, value):
    # PROBLEM --> 2 formats, with or without final 'Z' 
        if value is None:
            return ''

        dt = value.isoformat('T')
        dt = replace(dt,':','')
        dt = replace(dt,'-','')
        
        return dt   

    encode = classmethod(encode)


    def to_unicode(cls, value):
    # PROBLEM --> 2 formats, with or without final 'Z' 
        if value is None:
            return u''

        dt = value.isoformat('T')
        dt = replace(dt,u':',u'')
        dt = replace(dt,u'-',u'')

        return unicode(dt)   

    to_unicode = classmethod(to_unicode)


    def from_str(cls, value):
        if not value:
            return None
        date, time = value.split()
        year, month, day = date.split('-')
        year, month, day = int(year), int(month), int(day)
        hours, minutes, seconds = time.split(':')
        hours, minutes, seconds = int(hours), int(minutes), int(seconds)
        return datetime(year, month, day, hours, minutes, seconds)

    from_str = classmethod(from_str)


    def to_str(cls, value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')

    to_str = classmethod(to_str)

    

# Tokens
TNAME, TPARAM, TVALUE = range(3)
token_name = ['name', 'parameter', 'value']

# data types for each property
# --> TO VERIFY AND COMPLETE
# occurs = 0  means 0..n occurrences
data_properties = {
  'BEGIN':{'type': Unicode, 'occurs': 1}, \
  'END':{'type': Unicode, 'occurs': 1}, \
  'VERSION':{'type': Unicode, 'occurs': 1}, \
  'PRODID':{'type': Unicode, 'occurs': 1}, \
  'METHOD':{'type': Unicode, 'occurs': 1}, \
  # Component properties
  'ATTACH':{'type': URI, 'occurs': 0}, \
  'CATEGORY':{'type': Unicode, 'occurs': 1}, \
  'CATEGORIES':{'type': Unicode, 'occurs': 0}, \
  'CLASS':{'type': Unicode, 'occurs': 1}, \
  'COMMENT':{'type': Unicode, 'occurs': 0}, \
  'DESCRIPTION':{'type': Unicode, 'occurs': 1}, \
  'GEO':{'type': Unicode, 'occurs': 1}, \
  'LOCATION':{'type': Unicode, 'occurs': 1}, \
  'PERCENT-COMPLETE':{'type': Integer, 'occurs': 1}, \
  'PRIORITY':{'type': Integer, 'occurs': 1}, \
  'RESOURCES':{'type': Unicode, 'occurs': 0}, \
  'STATUS':{'type': Unicode, 'occurs': 1}, \
  'SUMMARY':{'type': Unicode, 'occurs': 1}, \
  # Date & Time component properties
  'COMPLETED':{'type': DateTime, 'occurs': 1}, \
  'DTEND':{'type': DateTime, 'occurs': 1}, \
  'DUE':{'type': DateTime, 'occurs': 1}, \
  'DTSTART':{'type': DateTime, 'occurs': 1}, \
  'DURATION':{'type': Unicode, 'occurs': 1}, \
  'FREEBUSY':{'type': Unicode, 'occurs': 1}, \
  'TRANSP':{'type': Unicode, 'occurs': 1}, \
  # Time Zone component properties
  'TZID':{'type': Unicode, 'occurs': 1}, \
  'TZNAME':{'type': Unicode, 'occurs': 0}, \
  'TZOFFSETFROM':{'type': Unicode, 'occurs': 1}, \
  'TZOFFSETTO':{'type': Unicode, 'occurs': 1}, \
  'TZURL':{'type': URI, 'occurs': 1}, \
  # Relationship component properties
  'ATTENDEE':{'type': URI, 'occurs': 0}, \
  'CONTACT':{'type': Unicode, 'occurs': 0}, \
  'ORGANIZER':{'type': URI, 'occurs': 1}, \
  # Recurrence component properties
  'EXDATE':{'type': DateTime, 'occurs': 0}, \
  'EXRULE':{'type': Unicode, 'occurs': 0}, \
  'RDATE':{'type': Unicode, 'occurs': 0}, \
  'RRULE':{'type': Unicode, 'occurs': 0}, \
  # Alarm component properties
  'ACTION':{'type': Unicode, 'occurs': 1}, \
  'REPEAT':{'type': Integer, 'occurs': 1}, \
  'TRIGGER':{'type': Unicode, 'occurs': 1}, \
  # Change management component properties
  'CREATED':{'type': DateTime, 'occurs': 1}, \
  'DTSTAMP':{'type': DateTime, 'occurs': 1}, \
  'LAST-MODIFIED':{'type': DateTime, 'occurs': 1}, \
  'SEQUENCE':{'type': Integer, 'occurs': 1}, \
  # Others
  'RECURRENCE-ID':{'type': DateTime, 'occurs': 1}, \
  'RELATED-TO':{'type': Unicode, 'occurs': 1}, \
  'URL':{'type': URI, 'occurs': 1}, \
  'UID':{'type': Unicode, 'occurs': 1}}

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
    # Lexical & syntaxic analysis
    #   status :
    #     0 --> initial status : (just before property name)
    #     1 --> property name begun
    #     2 --> parameter begun (just after ';')
    #     3 --> param-name begun 
    #     4 --> param-name ended, param-value beginning
    #     5 --> param-value quoted begun (just after '"')
    #     6 --> param-value NOT quoted begun 
    #     7 --> param-value ended (just after '"' for quoted ones)
    #     8 --> value to begin (just after ':')
    #     9 --> value begun 
    ###################################################################
    def get_tokens(cls, property):
        lexeme, status, last = '', 0, ''

        for c in property:
            # initial state : (just before property name)
            if status == 0:
                if c.isalnum() or c in ('-'):
                    lexeme, status = c, 1
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                    
            # property name begun
            elif status == 1:
                if c.isalnum() or c in ('-'):
                    lexeme += c
                elif c == ';':
                    status = 2
                    yield TNAME, lexeme
                elif c == ':':
                    status = 8
                    yield TNAME, lexeme
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)

            # parameter begun (just after ';')
            elif status == 2:
                if c.isalnum() or c in ('-'):
                    lexeme, status = c, 3
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                                    
            # param-name begun 
            elif status == 3:
                if c.isalnum() or c in ('-'):
                    lexeme += c
                elif c == '=':
                    lexeme += c
                    status = 4
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                    
            # param-name ended, param-value beginning
            elif status == 4:
                if c == '"':
                    lexeme += c
                    status = 5
                elif c in (';',':',',') :
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                else:    
                    lexeme += c
                    status = 6

            # param-value quoted begun (just after '"')
            elif status == 5:
                if c == '"':
                    lexeme += c
                    status = 7
                else:
                    lexeme += c
            
            # param-value NOT quoted begun 
            elif status == 6:
                if c in (':',';',',') :
                    status = 7
                elif c=='"':
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                else:    
                    lexeme += c
                    
            # value to begin (just after ':')
            elif status == 8:
                lexeme, status = c, 9

            # value begun 
            elif status == 9:
                lexeme += c
                
            # param-value ended (just after '"' for quoted ones)
            if status == 7:
                if c == ':':
                    status = 8
                    yield TPARAM, lexeme
                elif c == ';': 
                    status = 2
                    yield TPARAM, lexeme
                elif c == ',': 
                    lexeme += c
                    status = 4
                elif c == '"':
                    if last == '"':
                        raise SyntaxError, 'unexpected repeated character (%s)'\
                              ' at status %s' % (c, status)
                    last = '"'
                else:
                    raise SyntaxError, 'unexpected character (%s) at status %s'\
                                        % (c, status)
                    
        if status not in (8, 9):
            raise SyntaxError, 'unexpected property (%s)' % property
            
        yield TVALUE, lexeme

    get_tokens = classmethod(get_tokens)
    

    ###################################################################
    # Semantic analysis. 
    #
    #   XXX test if the property accepts the given parameters 
    #       could be a great idea
    # 
    #   property name  >  name
    #   parameter list >  parameters
    #   value          >  value
    # 
    ###################################################################
    def parse(cls, property, encoding='UTF-8'):
        name, value, parameters = None, None, {}

        for token, lexeme in PropertyType.get_tokens(property):
            if token == TNAME:
                name = lexeme
            elif token == TPARAM:
                param_name, param_value = lexeme.split('=')
                parameters[param_name] = ParameterType.decode(lexeme)
            elif token == TVALUE:
                #####################################
                # Change types of values when needed
                default_schema = {'type': String, 'occurs': 0 }
                schema = data_properties.get(name, default_schema)
                vtype = schema['type']
                if vtype is Unicode:
                    value = vtype.decode(lexeme, encoding)
                else:
                    value = vtype.decode(lexeme)
            else:
                raise SyntaxError, 'unexpected %s' % token_name[token]

        return name, value, parameters

    parse = classmethod(parse)


    def decode(cls, line, encoding='UTF-8'):
        name, value, parameters = None, None, {}
        # Parsing
        name, value, parameters = PropertyType.parse(line, encoding)
        from itools.ical.icalendar import Property
        return Property(name, value, parameters)

    decode = classmethod(decode)


    def to_unicode(cls, property):
        # Property name
        prop = unicode(property.name)
        # Property parameters
        if property.parameters:
            for key_param in property.parameters:
                prop = prop + u'\n ' + u';' + \
                       ParameterType.to_unicode(property.parameters[key_param])
        # Property value
        default_schema = {'type': String, 'occurs': 0 }
        schema = data_properties.get(property.name, default_schema)
        vtype = schema['type']
        value = vtype.to_unicode(property.value)
        prop = prop + u'\n :' + value
        # Property folded if necessary
        if len(prop)>75:
            prop = fold_line(prop)
        return prop

    to_unicode = classmethod(to_unicode)



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
    def parse(cls, parameter, encoding='UTF-8'):
        name, values = None, []
        name, values_str = parameter.split('=')
        values = values_str.split(',')
        return name, values

    parse = classmethod(parse)


    def decode(cls, parameter, encoding='UTF-8'):
        name, values = None, []

        # Parsing (omitting first character ';')
        name, values = ParameterType.parse(parameter, encoding)

        from itools.ical.icalendar import Parameter
        return Parameter(name, values)
        
    decode = classmethod(decode)


    def to_unicode(cls, parameter):
        # Parameter name
        param = unicode(parameter.name) + u'='
        # Parameter values
        param = param + unicode(parameter.values[0])
        for value in parameter.values[1:]:
            param = param + u',' + unicode(value)
        return param

    to_unicode = classmethod(to_unicode)



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
    #   - Regroup values of the same property into a list
    # 
    #   XXX test if number of occurrences of properties is correct
    # 
    ###################################################################
    def parse(cls, properties, c_type, encoding='UTF-8'):
        props = {}
        from pprint import pprint

        for property in properties:
            if property.name in props:
                occurs = 0
                if property.name in data_properties:
                    occurs = data_properties[property.name].get('occurs', 0)
                if occurs == 1:
                    pprint(props)
        #            raise SyntaxError, 'Property %s can be assigned only one '\
        #                               'value' % property.name
            else:
                props[property.name] = []

            props[property.name].append(property)

        return props

    parse = classmethod(parse)


    def decode(cls, properties, c_type, encoding='UTF-8'):
        props = {}

        # Parsing
        props = ComponentType.parse(properties, c_type, encoding)

        from itools.ical.icalendar import Component
        return Component(props, c_type)
        
    decode = classmethod(decode)


    def to_unicode(cls, component):
        lines = []
        
        lines.append('BEGIN:%s' % component.c_type)
    
        for key in component.properties:
            for item in component.properties[key]:
                lines.append(PropertyType.to_unicode(item))

        lines.append('END:%s' % component.c_type)
        
        return u'\n'.join(lines)

    to_unicode = classmethod(to_unicode)

