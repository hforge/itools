# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#               2005 Piotr Macuk <piotr@macuk.pl>
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
from datetime import date, datetime, time, timedelta, tzinfo
from time import strptime

# Import from itools
from base import DataType


###########################################################################
# RFC 822/1123
###########################################################################

class TZInfo(tzinfo):

    known_time_zones = {
        'GMT': 0, 'UTC': 0, 'UT': 0, # Greenwich Mean Time
        'EDT': -4, 'HAE': -4, # Eastern Daylight Time
        'EST': -5, 'HNE': -5, # Eastern Standard Time
        'CDT': -5, 'HAC': -5, # Central Daylight Time
        'CST': -6, 'HNC': -6, # Central Standard Time
        'MDT': -6, 'HAR': -6, # Mountain Daylight Time
        'MST': -7, 'HNR': -7, # Mountain Standard Time
        'PDT': -7, 'HAP': -7, # Pacific Daylight Time
        'PST': -8, 'HNP': -8  # Pacific Standard Time
    }

    def __init__(self, offset):
        # Offset as sign (+, -) and the number HHMM
        if offset[0] in ('+', '-'):
            # Strip zeros
            off = offset[1:].lstrip('0')
            # Offset in hours with sigh
            off = int(offset[0] + off) / 100
        elif self.known_time_zones.has_key(offset):
            off = self.known_time_zones[offset]
        else:
            off = 0
        self.__offset = timedelta(hours=off)
        self.__name = None


    def utcoffset(self, dt):
        return self.__offset


    def tzname(self, dt):
        return self.__name


    # Implementation without DST
    def dst(self, dt):
        return timedelta(0)



class InternetDateTime(DataType):

    @staticmethod
    def decode(value):
        # Remove the day name part if exists
        str = value.split(',')[-1].strip()
        # Split date and timezone part if exists
        datetime_parts = str.split(' ')
        date = ' '.join(datetime_parts[0:4])
        if len(datetime_parts) > 4:
            timezone = datetime_parts[4]
        else:
            # UTC is the default timezone
            timezone = 'UTC'
        dt = strptime(date, '%d %b %Y %H:%M:%S')
        tz = TZInfo(timezone)
        return datetime(dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], 0, tz)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        else:
            utc = TZInfo('UTC')
            return value.astimezone(utc).strftime('%Y-%m-%d %H:%M:%S')



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
            return date(year, 1, 1)

        # Extended format
        if data[0] == '-':
            data = data[1:]
            month = int(data[:2])
            data = data[2:]
            if not data:
                return date(year, month, 1)
            # The day
            day = int(data[1:])
            return date(year, month, day)

        # Basic format
        month = int(data[:2])
        data = data[2:]
        if not data:
            return date(year, month, 1)
        # The day
        day = int(data)
        return date(year, month, day)


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
            return time(hour)

        # Extended format
        if data[0] == ':':
            data = data[1:]
            minute = int(data[:2])
            data = data[2:]
            if not data:
                return time(hour, minute)
            # The day
            second = int(data[1:])
            return time(hour, minute, second)

        # Basic format
        minute = int(data[:2])
        data = data[2:]
        if not data:
            return time(hour, minute)
        # The day
        second = int(data)
        return time(hour, minute, second)


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

