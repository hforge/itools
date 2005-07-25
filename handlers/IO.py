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

# Import from itools
from itools import uri



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


    def to_unicode(cls, value, encoding='UTF-8'):
        # Escape XML (XXX this is specific to XML)
        value = unicode(value, encoding)
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
        return unicode(value)

    to_unicode = classmethod(to_unicode)
