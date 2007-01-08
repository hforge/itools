# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import datetime
import mimetypes
import decimal

# Import from itools
from itools.uri import get_reference
from itools.i18n import languages as i18n_languages
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


class Time(DataType):
 
    @staticmethod
    def decode(value):
        if not value:
            return None
        values = value.split(':')
        hours = values.pop(0)
        minutes = values.pop(0)
        seconds = 0
        if values:
            seconds = values.pop(0)
        hours, minutes, seconds = int(hours), int(minutes), int(seconds)
        return datetime.time(hours, minutes, seconds)


    @staticmethod
    def encode(value, seconds=True):
        if value is None:
            return ''
        if not seconds:
            return value.strftime('%H:%M')
        return value.strftime('%H:%M:%S')



class DateTime(DataType):

    @staticmethod
    def decode(value):
        if not value:
            return None
        date, time = value.split()
        date = Date.decode(date)
        time = Time.decode(time)

        return datetime.datetime.combine(date, time)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')



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
        return re.match("^[0-9a-z]+[_\.0-9a-z-'+]*@([0-9a-z][0-9a-z-]+\.)+[a-z]{2,4}$",
                        value.lower()) is not None



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
            elif data[-1] in i18n_languages:
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
            elif data[-1] in i18n_languages:
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
