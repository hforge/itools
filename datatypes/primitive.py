# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import decimal
import mimetypes
import re

# Import from itools
from itools.uri import get_reference
from itools.i18n import has_language
from base import DataType



def is_datatype(type, base_type):
    """
    Returns True if 'type' is of 'base_type'.
    """
    try:
        if issubclass(type, base_type):
            return True
    except TypeError:
        pass
    if isinstance(type, base_type):
        return True
    return False
 


class Integer(DataType):

    @staticmethod
    def decode(value):
        if not value:
            return None
        return int(value)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value)



class Decimal(DataType):

    @staticmethod
    def decode(value):
        if not value:
            return None
        return decimal.Decimal(value)

    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value)



class Unicode(DataType):

    default = u''


    @staticmethod
    def decode(value, encoding='UTF-8'):
        return unicode(value, encoding)


    @staticmethod
    def encode(value, encoding='UTF-8'):
        return value.encode(encoding)



class String(DataType):

    @staticmethod
    def decode(value):
        return value


    @staticmethod
    def encode(value):
        return value



class Boolean(DataType):
    
    default = False

    @staticmethod
    def decode(value):
        return bool(int(value))


    @staticmethod
    def encode(value):
        if value is True:
            return '1'
        elif value is False:
            return '0'
        else:
            raise ValueError, 'value is not a boolean'



class URI(DataType):

    @staticmethod
    def decode(value):
        return get_reference(value)


    @staticmethod
    def encode(value):
        return str(value)



class Email(String):

    @staticmethod
    def is_valid(value):
        expr = "^[0-9a-z]+[_\.0-9a-z-'+]*@([0-9a-z][0-9a-z-]+\.)+[a-z]{2,4}$"
        return re.match(expr, value.lower()) is not None



class FileName(DataType):
    """
    A filename is tuple consisting of a name, a type and a language.

    XXX We should extend this to add the character encoding
    """

    @staticmethod
    def decode(data):
        data = data.split('.')

        # XXX The encoding (UTF-8, etc.)

        n = len(data)
        if n == 1:
            return data[0], None, None
        elif n == 2:
            if '.%s' % data[-1].lower() in mimetypes.types_map:
                name, type = data
                return name, type, None
            elif has_language(data[-1]):
                name, language = data
                return name, None, language
            else:
                return '.'.join(data), None, None
        else:
            # Default values
            type = encoding = language = None

            # The language
            if '.%s' % data[-1].lower() in mimetypes.encodings_map:
                encoding = data[-1]
                data = data[:-1]
            elif has_language(data[-1]):
                language = data[-1]
                data = data[:-1]

            # The type
            if '.%s' % data[-1].lower() in mimetypes.types_map:
                type = data[-1]
                data = data[:-1]

            if encoding is not None:
                type = '%s.%s' % (type, encoding)

            # The name
            name = '.'.join(data)

        return name, type, language


    @staticmethod
    def encode(value):
        name, type, language = value
        if type is not None:
            name = name + '.' + type
        if language is not None:
            name = name + '.' + language
        return name



class QName(DataType):

    @staticmethod
    def decode(data):
        if ':' in data:
            return tuple(data.split(':', 1))

        return None, data


    @staticmethod
    def encode(value):
        if value[0] is None:
            return value[1]
        return '%s:%s' % value



class Tokens(DataType):

    @staticmethod
    def decode(data):
        return tuple(data.split())


    @staticmethod
    def encode(value):
        return ' '.join(value)



class Enumerate(String):

    is_enumerate = True

    options = []


    @classmethod
    def is_valid(cls, value):
        for option in cls.options:
            if value == option['name']:
                return True
        return False


    @classmethod
    def get_options(cls):
        """Returns a copy of options list of dictionaries."""
        return [dict(option) for option in cls.options]


    @classmethod
    def get_namespace(cls, name):
        options = cls.get_options()
        if type(name) is type([]):
            for option in options:
                option['selected'] = option['name'] in name
        else:
            for option in options:
                option['selected'] = option['name'] == name
        return options


    @classmethod
    def get_value(cls, name, default=None):
        for option in cls.options:
            if option['name'] == name:
                return option['value']

        return default


############################################################################
# Medium decoder/encoders (not for values)

class XML(object):

    @staticmethod
    def encode(value):
        return value.replace('&', '&amp;').replace('<', '&lt;')


    @staticmethod
    def decode(value):
        return value.replace('&amp;', '&').replace('&lt;', '<')



class XMLAttribute(object):

    @staticmethod
    def encode(value):
        value = value.replace('&', '&amp;').replace('<', '&lt;')
        return value.replace('"', '&quot;')

    @staticmethod
    def decode(value):
        value = value.replace('&amp;', '&').replace('&lt;', '<')
        return value.replace('&quot;', '"')
