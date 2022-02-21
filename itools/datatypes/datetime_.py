# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2008, 2011-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
# Copyright (C) 2007 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
# Copyright (C) 2011 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2012 Nicolas Deram <nderam@gmail.com>
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
from calendar import timegm
from datetime import date, datetime, time
from email.utils import parsedate_tz, formatdate
from time import mktime

# Import from itools
from itools.core import fixed_offset
from .base import DataType


###########################################################################
# Parsing the wide family of date formats in Internet protocols
###########################################################################

class HTTPDate(DataType):
    """The behaviour of this datatype is as described in RFC 2616 (HTTP 1.1)
    """

    @staticmethod
    def decode(data):
        """Decode dates in formats RFC 1123 (inc. 822), RFC-850, ANSI C's
        asctime() format, and non-standard formats sent by some HTTP
        clients.
        """
        # Parse the date into a tuple, including the timezone
        parts = parsedate_tz(data)
        if parts is None:
            raise ValueError('date "%s" is not supported' % data)
        parts, tz = parts[:9], parts[9]

        # Get a naive datetime
        timestamp = mktime(parts)
        naive_dt = datetime.fromtimestamp(timestamp)

        # Return an aware datetime (if tz is None assume GMT)
        if tz is None:
            tz = 0
        tz = fixed_offset(tz/60)
        return tz.localize(naive_dt)

    @staticmethod
    def encode(value):
        """Encode a datetime object to RFC 1123 format: ::

            Day, DD Month YYYY HH:MM:SS GMT

        "Day" and "Month" are the English names abbreviated.
        """
        # Datetime to unix timestamp in utc
        parts = value.utctimetuple()
        timestamp = timegm(parts)

        # Serialize timestamp to a RFC-2822 string (always GMT)
        return formatdate(timestamp, usegmt=True)



###########################################################################
# ISO 8601 (http://en.wikipedia.org/wiki/ISO_8601)
###########################################################################

# XXX Python dates (the datetime.date module) require the month and day,
# they are not able to represent lower precision dates as ISO 8601 does.
# In the long run we will need to replace Python dates by something else.
class ISOCalendarDate(DataType):
    """Extended formats (from max. to min. precision): %Y-%m-%d, %Y-%m, %Y

    Basic formats: %Y%m%d, %Y%m, %Y
    """
    format_date = '%Y-%m-%d'
    sep_date = '-'

    @classmethod
    def decode(cls, data):
        if not data:
            return None
        format_date = cls.format_date
        sep_date = cls.sep_date

        values = data.split(cls.sep_date)
        year, month, day = 1, 1, 1

        for i, key in enumerate(format_date.split(sep_date)):
            if i >= len(values):
                break
            value = int(values[i])
            if key == '%Y':
                year = value
            elif key == '%m':
                month = value
            elif key == '%d':
                day = value

        return date(year, month, day)

    @classmethod
    def encode(cls, value):
        # We choose the extended format as the canonical representation
        if value is None:
            return ''
        return value.strftime(cls.format_date)

    @classmethod
    def is_valid(cls, value):
        # Only consider the value is valid if we are able to encode it.
        # Specifically this covers dates before 1900, which are not supported
        # by strftime (in Python 2, because Python 3 does support them).
        try:
            cls.encode(value)
        except Exception:
            return False
        return True


# TODO ISOWeekDate
# TODO ISOOrdinalDate

class ISOTime(DataType):
    """Extended formats (from max. to min. precision): %H:%M:%S.%f, %H:%M:%S, %H:%M

    Basic formats: %H%M%S%f, %H%M%S, %H%M, %H
    """

    @staticmethod
    def decode(data):
        if not data:
            return None

        # Timezone
        if data[-1] == 'Z':
            data = data[:-1]
            tzinfo = fixed_offset(0)
        else:
            p_pos = data.find('+')
            m_pos = data.find('-')
            pos = m_pos * p_pos
            if pos > 0:
                tzinfo = None
            else:
                pos = -pos
                sign = data[pos]
                offset = data[pos+1:]
                if ':' in offset:
                    offset = offset.split(':')
                else:
                    offset = [offset[0:2], offset[2:]]
                o_h = int(offset[0])
                o_m = int(offset[1]) if offset[1] else 0
                data = data[:pos]
                offset = (o_h * 60 + o_m)
                if sign == '-':
                    offset = -offset
                tzinfo = fixed_offset(offset)

        # Extended formats
        if ':' in data:
            parts = data.split(':')
            n = len(parts)
            if n > 3:
                raise ValueError('unexpected time value "%s"' % data)
            hour = int(parts[0])
            minute = int(parts[1])
            if n == 2:
                return time(hour, minute, tzinfo=tzinfo)
            data = parts[2]
            if '.' not in data:
                second = int(data)
                return time(hour, minute, second, tzinfo=tzinfo)
            parts = data.split('.')
            n = len(parts)
            if n > 2:
                raise ValueError('unexpected time value "%s"' % data)
            second = int(parts[0])
            microsecond = int(parts[1])
            return time(hour, minute, second, microsecond, tzinfo=tzinfo)

        # Basic formats
        hour = int(data[:2])
        data = data[2:]
        if not data:
            return time(hour, tzinfo=tzinfo)
        # Minute
        minute = int(data[:2])
        data = data[2:]
        if not data:
            return time(hour, minute, tzinfo=tzinfo)
        # Second
        second = int(data[:2])
        data = data[2:]
        if not data:
            return time(hour, minute, second, tzinfo=tzinfo)
        # Microsecond
        microsecond = int(data)
        return time(hour, minute, second, microsecond, tzinfo=tzinfo)

    @staticmethod
    def encode(value):
        # We choose the extended format as the canonical representation
        if value is None:
            return ''
        fmt = '%H:%M:%S.%f'
        if value.tzinfo is not None:
            fmt += '%Z'
        return value.strftime(fmt)


class ISODateTime(DataType):

    cls_date = ISOCalendarDate
    time_is_required = True

    def decode(self, value):
        if not value:
            return None
        if type(value) is bytes:
            value = value.decode("utf-8")
        value = value.split('T')
        date, time = value[0], value[1:]

        date = self.cls_date.decode(date)
        if time:
            time = ISOTime.decode(time[0])
            return datetime.combine(date, time)

        if self.time_is_required:
            raise ValueError('expected time field not found')

        return date

    def encode(self, value):
        if value is None:
            return ''
        fmt_date = self.cls_date.format_date
        value_type = type(value)
        if value_type is datetime:
            # Datetime
            fmt = fmt_date + 'T%H:%M:%S.%f'
            if value.tzinfo is not None:
                fmt += '%z'
        elif value_type is date and not self.time_is_required:
            # Date
            fmt = fmt_date
        else:
            # Error
            raise TypeError("unexpected value of type '%s'" % value_type)

        return value.strftime(fmt)
