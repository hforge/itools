# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import mimetypes

# Import from itools
from itools import uri
from itools import i18n
from base import DataType



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



class Unicode(DataType):

    default = u''


    @staticmethod
    def decode(value, encoding='UTF-8'):
        return unicode(value, encoding)


    @staticmethod
    def encode(value, encoding='UTF-8'):
        # Escape XML (XXX this is specific to XML)
        value = value.replace('&', '&amp;').replace('<', '&lt;')
        return value.encode(encoding)



class String(DataType):

    @staticmethod
    def decode(value):
        return value


    @staticmethod
    def encode(value):
        return value



class Boolean(DataType):

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



class Date(DataType):
 
    @staticmethod
    def decode(value):
        if not value:
            return None
        year, month, day = value.split('-')
        year, month, day = int(year), int(month), int(day)
        return datetime.date(year, month, day)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d')



class DateTime(DataType):

    @staticmethod
    def decode(value):
        if not value:
            return None
        date, time = value.split()
        year, month, day = date.split('-')
        year, month, day = int(year), int(month), int(day)
        hours, minutes = time.split(':')
        hours, minutes = int(hours), int(minutes)
        return datetime.datetime(year, month, day, hours, minutes)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M')



class URI(DataType):

    @staticmethod
    def decode(value):
        return uri.get_reference(value)


    @staticmethod
    def encode(value):
        return str(value).replace('&', '&amp;')



class FileName(DataType):
    """
    A filename is tuple consisting of a name, a type and a language.

    XXX We should extend this to add the character encoding and the
    compression (gzip, bzip, etc.).
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
            elif data[-1] in i18n.languages:
                name, language = data
                return name, None, language
            else:
                return '.'.join(data), None, None
        else:
            # Default values
            type = language = None

            # The language
            if data[-1] in i18n.languages:
                language = data[-1]
                data = data[:-1]

            # The type
            if '.%s' % data[-1].lower() in mimetypes.types_map:
                type = data[-1]
                data = data[:-1]

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
