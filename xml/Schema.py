# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import datetime



############################################################################
# Simple Types
############################################################################
class SimpleType(object):
    pass


class Integer(SimpleType):
    def encode(cls, value):
        if value is None:
            return ''
        return unicode(value)
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        if not value:
            return None
        return int(value)
    decode = classmethod(decode)


class Unicode(SimpleType):
    def encode(cls, value):
        return value.replace('&', '&amp;').replace('<', '&lt;')
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        return value
    decode = classmethod(decode)


class String(SimpleType):
    def encode(cls, value):
        return unicode(value)
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        return str(value)
    decode = classmethod(decode)


class Boolean(SimpleType):
    def encode(cls, value):
        if value is True:
            return '1'
        elif value is False:
            return '0'
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        return bool(int(value))
    decode = classmethod(decode)
  

class Date(SimpleType):
    def encode(cls, value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d')
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        if not value:
            return None
        year, month, day = value.split('-')
        year, month, day = int(year), int(month), int(day)
        return datetime.date(year, month, day)
    decode = classmethod(decode)


class DateTime(SimpleType):
    def encode(cls, value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M')
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        if not value:
            return None
        date, time = value.split()
        year, month, day = date.split('-')
        year, month, day = int(year), int(month), int(day)
        hours, minutes = time.split(':')
        hours, minutes = int(hours), int(minutes)
        return datetime.datetime(year, month, day, hours, minutes)
    decode = classmethod(decode)


############################################################################
# Complex Types
############################################################################
class ComplexType(object):
    schema = {}


    def __init__(self, **kw):
        schema = self.schema
        for key, value in kw.items():
            if key in schema:
                self.set_property(key, value)


    def encode(self):
        schema = self.schema
        data = u''

        property_names = schema.keys()
        property_names.sort()
        for name in property_names:
            type, default = schema[name]
            if hasattr(self, name):
                value = getattr(self, name)
                if isinstance(value, dict):
                    # Multilingual
                    for language, value in value.items():
                        value = type.encode(value)
                        data += u'<%s lang="%s">%s</%s>\n' \
                                % (name, language, value, name)
                else:
                    if isinstance(value, list):
                        values = value
                    else:
                        values = [value]
                    for value in values:
                        value = type.encode(value)
                        if issubclass(type, ComplexType):
                            data += u'<%s>\n' % name
                            value = [ '  %s\n' % x
                                      for x in value.splitlines() ]
                            data += ''.join(value)
                            data += u'</%s>\n' % name
                        else:
                            data += u'<%s>%s</%s>\n' % (name, value, name)
        return data


    def decode(cls, node):
        schema = cls.schema
        property = cls()
        for node in node.get_elements():
            name = node.name
            # Decode the value
            type, default = schema[name]
            if issubclass(type, SimpleType):
                value = unicode(node.children)
                value = type.decode(value)
            elif issubclass(type, ComplexType):
                value = type.decode(node)
            else:
                raise ValueError, 'bad type for "%s"' % name
            # The language
            if 'lang' in node.attributes:
                language = node.attributes['lang'].value
            else:
                language = None
            # Set property value
            property.set_property(name, value, language=language)
        return property
    decode = classmethod(decode)


    def get_property(self, name):
        schema = self.schema
        if name not in schema:
            raise LookupError, 'schema does not define property "%s"' % name
        type, default = schema[name]
        return getattr(self, name, default)


    def set_property(self, name, value, language=None):
        if language is None:
            type, default = self.schema[name]
            if isinstance(default, list):
                if isinstance(value, list):
                    setattr(self, name, value)
                else:
                    if not hasattr(self, name):
                        setattr(self, name, [])
                    values = getattr(self, name)
                    values.append(value)
            else:
                setattr(self, name, value)
        else:
            if not hasattr(self, name):
                setattr(self, name, {})
            values = getattr(self, name)
            values[language] = value
