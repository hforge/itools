# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2008 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from decimal import Decimal as decimal
from re import match
from copy import deepcopy

# Import from itools
from itools.core import freeze
from itools.uri import Path, get_reference
from base import DataType


class Integer(DataType):

    @staticmethod
    def decode(value):
        if value == '':
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
        if value == '':
            return None
        return decimal(value)

    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value)



class Unicode(DataType):

    default = u''


    @classmethod
    def get_default(cls):
        return cls.default


    @staticmethod
    def decode(value, encoding='UTF-8'):
        return unicode(value, encoding)


    @staticmethod
    def encode(value, encoding='UTF-8'):
        return value.encode(encoding)


    @staticmethod
    def is_empty(value):
        return value.strip() == u''



class String(DataType):

    @staticmethod
    def decode(value):
        return value


    @staticmethod
    def encode(value):
        if value is None:
            return ''
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



class URI(String):
    # XXX Should we at least normalize the sring when decoding/encoding?

    @staticmethod
    def is_valid(value):
        try:
            get_reference(value)
        except:
            return False
        return True



class PathDataType(DataType):
    # TODO Do like URI, do not decode (just an string), and use 'is_valid'
    # instead

    default = Path('')

    @staticmethod
    def decode(value):
        return Path(value)


    @staticmethod
    def encode(value):
        return str(value)



class Email(String):

    @staticmethod
    def is_valid(value):
        expr = "^[0-9a-z]+[_\.0-9a-z-'+]*@([0-9a-z][0-9a-z-]+\.)+[a-z]{2,4}$"
        return match(expr, value.lower()) is not None



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

    default = ()

    @staticmethod
    def decode(data):
        return tuple(data.split())


    @staticmethod
    def encode(value):
        return ' '.join(value)



class MultiLinesTokens(DataType):

    @staticmethod
    def decode(data):
        return tuple(data.splitlines())


    @staticmethod
    def encode(value):
        return '\n'.join(value)




###########################################################################
# Enumerates

class Enumerate(String):

    is_enumerate = True
    options = freeze([])


    @classmethod
    def get_options(cls):
        """Returns a list of dictionaries in the format
            [{'name': <str>, 'value': <unicode>}, ...]
        The default implementation returns a copy of the "options" class
        attribute. Both the list and the dictionaries may be modified
        afterwards.
        """
        return deepcopy(cls.options)


    @classmethod
    def is_valid(cls, name):
        """Returns True if the given name is part of this Enumerate's options.
        """
        options = cls.get_options()
        return enumerate_is_valid(options, name)


    @classmethod
    def get_namespace(cls, name):
        """Extends the options with information about which one is matching
        the given name.
        """
        options = cls.get_options()
        return enumerate_get_namespace(options, name)


    @classmethod
    def get_value(cls, name, default=None):
        """Returns the value matching the given name, or the default value.
        """
        options = cls.get_options()
        return enumerate_get_value(options, name, default)



# TODO suppress now there is a single Enumerate class?
def enumerate_is_valid(options, name):
    for option in options:
        if name == option['name']:
            return True
    return False


def enumerate_get_namespace(options, name):
    if isinstance(name, list):
        for option in options:
            option['selected'] = option['name'] in name
    else:
        for option in options:
            option['selected'] = option['name'] == name
    return options


def enumerate_get_value(options, name, default=None):
    for option in options:
        if option['name'] == name:
            return option['value']

    return default


###########################################################################
# Medium decoder/encoders (not for values)
###########################################################################

class XMLContent(object):

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
