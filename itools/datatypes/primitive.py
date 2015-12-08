# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006-2008, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007, 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2007, 2011 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2009 Nicolas Deram <nderam@gmail.com>
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
from copy import deepcopy
from decimal import Decimal as decimal
from json import loads, dumps
from re import compile

# Import from itools
from itools.core import freeze
from itools.uri import Path, get_reference

# Import from here
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


    @staticmethod
    def decode(value, encoding='UTF-8'):
        return unicode(value, encoding).strip()


    @staticmethod
    def encode(value, encoding='UTF-8'):
        return value.strip().encode(encoding)


    @staticmethod
    def is_empty(value):
        return value == u''



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
        except Exception:
            return False
        return True


    @staticmethod
    def is_empty(value):
        return not value



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



# We consider the local part in emails is case-insensitive. This is against
# the standard, but corresponds to common usage.
email_expr = "^[0-9a-z]+[_\.0-9a-z-'+]*@([0-9a-z-]+\.)+[a-z]{2,6}$"
email_expr = compile(email_expr)
class Email(String):

    @staticmethod
    def encode(value):
        return value.lower() if value else value

    @staticmethod
    def decode(value):
        return value.lower()

    @staticmethod
    def is_valid(value):
        return email_expr.match(value) is not None



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


    def get_options(cls):
        """Returns a list of dictionaries in the format
            [{'name': <str>, 'value': <unicode>}, ...]
        The default implementation returns a copy of the "options" class
        attribute. Both the list and the dictionaries may be modified
        afterwards.
        """
        return deepcopy(cls.options)


    def is_valid(self, name):
        """Returns True if the given name is part of this Enumerate's options.
        """
        options = self.get_options()
        if isinstance(name, list):
            options = set([option['name'] for option in options])
            return set(name).issubset(options)
        for option in options:
            if name == option['name']:
                return True
        return False


    def get_namespace(cls, name):
        """Extends the options with information about which one is matching
        the given name.
        """
        options = cls.get_options()
        return enumerate_get_namespace(options, name)


    def get_value(cls, name, default=None):
        """Returns the value matching the given name, or the default value.
        """
        options = cls.get_options()
        return enumerate_get_value(options, name, default)


def enumerate_get_namespace(options, name):
    if type(name) is list:
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


###########################################################################
# JSON
###########################################################################
class JSONObject(DataType):
    """A JSON object, which is a Python dict serialized as a JSON string.

    See also JSONArray
    """

    default = {}

    @staticmethod
    def is_valid(value):
        return isinstance(value, dict)


    @staticmethod
    def decode(value):
        from itools.web.utils import fix_json
        value = loads(value)
        return fix_json(value)


    @staticmethod
    def encode(value):
        from itools.web.utils import NewJSONEncoder
        return dumps(value, cls=NewJSONEncoder)



class JSONArray(JSONObject):
    """A JSON array, which is a Python list serialized as a JSON string

    See also JSONObject
    """

    default = []


    @staticmethod
    def is_valid(value):
        return isinstance(value, list)
