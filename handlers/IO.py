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



class Integer(object):
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


class Unicode(object):
    def encode(cls, value):
        return value.replace('&', '&amp;').replace('<', '&lt;')
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        return value
    decode = classmethod(decode)


class String(object):
    def encode(cls, value):
        return unicode(value)
    encode = classmethod(encode)


    def decode(cls, value):
        value = value.strip()
        return str(value)
    decode = classmethod(decode)


class Boolean(object):
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
  

class Date(object):
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


class DateTime(object):
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
