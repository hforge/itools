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



class Integer(object):

    def decode(cls, value):
        if not value:
            return None
        return int(value)

    decode = classmethod(decode)


    def encode(cls, value):
        if value is None:
            return ''
        return str(value)

    encode = classmethod(encode)


    def to_unicode(cls, value):
        if value is None:
            return u''
        return unicode(value)

    to_unicode = classmethod(to_unicode)



class Unicode(object):

    def decode(cls, value, encoding='UTF-8'):
        return unicode(value, encoding)

    decode = classmethod(decode)


    def encode(cls, value, encoding='UTF-8'):
        # Escape XML (XXX this is specific to XML)
        value = value.replace('&', '&amp;').replace('<', '&lt;')
        return value.encode(encoding)

    encode = classmethod(encode)


    def to_unicode(cls, value):
        # Escape XML (XXX this is specific to XML)
        value = value.replace('&', '&amp;').replace('<', '&lt;')
        return value

    to_unicode = classmethod(to_unicode)



class String(object):

    def decode(cls, value):
        return value

    decode = classmethod(decode)


    def encode(cls, value):
        return value

    encode = classmethod(encode)


    def to_unicode(cls, value):
        return unicode(value)

    to_unicode = classmethod(to_unicode)



class Boolean(object):

    def decode(cls, value):
        return bool(int(value))

    decode = classmethod(decode)


    def encode(cls, value):
        if value is True:
            return '1'
        elif value is False:
            return '0'
        else:
            raise ValueError, 'value is not a boolean'

    encode = classmethod(encode)


    def to_unicode(cls, value):
        if value is True:
            return u'1'
        elif value is False:
            return u'0'
        else:
            raise ValueError, 'value is not a boolean'

    to_unicode = classmethod(to_unicode)



class Date(object):

    def decode(cls, value):
        if not value:
            return None
        year, month, day = value.split('-')
        year, month, day = int(year), int(month), int(day)
        return datetime.date(year, month, day)

    decode = classmethod(decode)


    def encode(cls, value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d')

    encode = classmethod(encode)


    def to_unicode(cls, value):
        if value is None:
            return u''
        return unicode(value.strftime('%Y-%m-%d'))

    to_unicode = classmethod(to_unicode)



class DateTime(object):

    def decode(cls, value):
        if not value:
            return None
        date, time = value.split()
        year, month, day = date.split('-')
        year, month, day = int(year), int(month), int(day)
        hours, minutes = time.split(':')
        hours, minutes = int(hours), int(minutes)
        return datetime.datetime(year, month, day, hours, minutes)

    decode = classmethod(decode)


    def encode(cls, value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M')

    encode = classmethod(encode)


    def to_unicode(cls, value):
        if value is None:
            return u''
        return unicode(value.strftime('%Y-%m-%d %H:%M'))

    to_unicode = classmethod(to_unicode)



class URI(object):

    def decode(cls, value):
        return uri.get_reference(value)

    decode = classmethod(decode)


    def encode(cls, value):
        return str(value)

    encode = classmethod(encode)


    def to_unicode(cls, value):
        return unicode(value).replace(u'&', u'&amp;')

    to_unicode = classmethod(to_unicode)



class FileName(object):
    """
    A filename is tuple consisting of a name, a type and a language.

    XXX We should extend this to add the character encoding and the
    compression (gzip, bzip, etc.).
    """

    def decode(cls, data):
        data = data.split('.')

        # XXX The encoding (UTF-8, etc.)

        n = len(data)
        if n == 1:
            return data[0], None, None
        elif n == 2:
            if '.%s' % data[-1] in mimetypes.types_map:
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
            if '.%s' % data[-1] in mimetypes.types_map:
                type = data[-1]
                data = data[:-1]

            # The name
            name = '.'.join(data)

        return name, type, language

    decode = classmethod(decode)


    def encode(cls, value):
        name, type, language = value
        if type is not None:
            name = name + '.' + type
        if language is not None:
            name = name + '.' + language
        return name

    encode = classmethod(encode)



class QName(object):

    def decode(cls, data):
        if ':' in data:
            return tuple(data.split(':', 1))

        return None, data

    decode = classmethod(decode)


    def encode(cls, value):
        if value[0] is None:
            return value[1]
        return '%s:%s' % value

    encode = classmethod(encode)



class Tokens(object):

    def decode(cls, data):
        return tuple(data.split())

    decode = classmethod(decode)


    def encode(cls, value):
        return ' '.join(value)

    encode = classmethod(encode)


    def to_unicode(cls, value):
        return u' '.join(value)

    to_unicode = classmethod(to_unicode)
