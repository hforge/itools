# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import datetime

# Import from itools
from base import DataType


###########################################################################
# ISO 8601 (http://en.wikipedia.org/wiki/ISO_8601)
###########################################################################

# XXX Python dates (the datetime.date module) require the month and day,
# they are not able to represent lower precission dates as ISO 8601 does.
# In the long run we will need to replace Python dates by something else.

class ISOCalendarDate(DataType):
    """
    Extended formats (from max. to min. precission): %Y-%m-%d, %Y-%m, %Y

    Basic formats: %Y%m%d, %Y%m, %Y
    """
 
    @staticmethod
    def decode(data):
        if not data:
            return None
        
        # The year
        year = int(data[:4])
        data = data[4:]
        if not data:
            return datetime.date(year, 1, 1)

        # Extended format
        if data[0] == '-':
            data = data[1:]
            month = int(data[:2])
            data = data[2:]
            if not data:
                return datetime.date(year, month, 1)
            # The day
            day = int(data[1:])
            return datetime.date(year, month, day)

        # Basic format
        month = int(data[:2])
        data = data[2:]
        if not data:
            return datetime.date(year, month, 1)
        # The day
        day = int(data)
        return datetime.date(year, month, day)


    @staticmethod
    def encode(value):
        # We choose the extended format as the canonical representation
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d')


# TODO ISOWeekDate
# TODO ISOOrdinalDate


class ISOTime(DataType):
    """
    Extended formats (from max. to min. precission): %H:%M:%S, %H:%M, %H

    Basic formats: %H%M%S, %H%M, %H
    """
 
    @staticmethod
    def decode(data):
        if not data:
            return None

        # The hour
        hour = int(data[:2])
        data = data[2:]
        if not data:
            return datetime.time(hour)

        # Extended format
        if data[0] == ':':
            data = data[1:]
            minute = int(data[:2])
            data = data[2:]
            if not data:
                return datetime.time(hour, minute)
            # The day
            second = int(data[1:])
            return datetime.time(hour, minute, second)

        # Basic format
        minute = int(data[:2])
        data = data[2:]
        if not data:
            return datetime.time(hour, minute)
        # The day
        second = int(data)
        return datetime.time(hour, minute, second)


    @staticmethod
    def encode(value):
        # We choose the extended format as the canonical representation
        if value is None:
            return ''
        return value.strftime('%H:%M:%S')



class ISODateTime(DataType):

    @staticmethod
    def decode(value):
        if not value:
            return None
        date, time = value.split('T')
        date = ISOCalendarDate.decode(date)
        time = ISOTime.decode(time)

        return datetime.combine(date, time)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%dT%H:%M:%S')



###########################################################################
# XXX Backwards compatibility
###########################################################################
class DateTime(DataType):

    @staticmethod
    def decode(value):
        if not value:
            return None
        date, time = value.split()
        date = ISOCalendarDate.decode(date)
        time = ISOTime.decode(time)

        return datetime.datetime.combine(date, time)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return value.strftime('%Y-%m-%d %H:%M:%S')

