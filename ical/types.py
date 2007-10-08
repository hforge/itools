# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2005-2007 Nicolas Deram <nicolas@itaapy.com>
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

# Import from Python Standard Library
from datetime import datetime

# Import from itools
from itools.datatypes import DataType, Integer, ISOTime , URI, Unicode, String


class Time(ISOTime):
    """
    This datatype is the same as ISOTime except that its encode method don't use
    seconds if not explicitely notified.
    """
    @staticmethod
    def encode(value, seconds=False):
        if value is None:
            return ''
        if not seconds:
            return value.strftime('%H:%M')
        return value.strftime('%H:%M:%S')



class DateTime(DataType):
    """
    iCalendar Date format:

    DTSTART:19970714T133000.000000 (Local time)

    DTSTART:19970714T173000Z (UTC time)

    DTSTART;TZID=US-Eastern:19970714T133000 (Local time and time zone reference)
    """

    @staticmethod
    def decode(value):
        if value is None:
            return None

        year, month, day, hour, min, sec, micro = 0, 0, 0, 0, 0, 0, 0
        date = value[:8]
        year, month, day = int(date[:4]), int(date[4:6]), int(date[6:8])

        # Time can be omitted
        if 'T' in value:
            time = value[9:]

            # ignore final Z for now
            if time[-1] == 'Z':
                time = time[:-1]
            else:
                pass
                # a parameter can have be added with utc info
                # ...

            hour, min = int(time[:2]), int(time[2:4])
            if '.' in time:
                sec, micro = time.split('.')
                sec = int(sec[-2:])
                micro = int(micro)
            elif len(time) >= 6:
                sec = int(time[4:6])

        return datetime(year, month, day, hour, min, sec, micro)


    @staticmethod
    def encode(value):
    # PROBLEM --> 2 formats, with or without final 'Z'
        if value is None:
            return ''

        dt = value.isoformat('T')
        dt = dt.replace(':','')
        dt = dt.replace('-','')

        return dt


    @staticmethod
    def from_str(value):
        if not value:
            return None
        date, time = value, None
        if ' ' in value:
            date, time = value.split()
        # Date
        year, month, day = date.split('-')
        year, month, day = int(year), int(month), int(day)
        # If no time
        if not time:
             return datetime(year, month, day)
        # Time
        if time.count(':') == 1:
            hours, minutes = time.split(':')
            hours, minutes, seconds, micro = int(hours), int(minutes), 0, 0
        else:
            hours, minutes, seconds = time.split(':')
            if '.' in seconds:
                seconds, micro = seconds.split('.')
                micro = int(micro)
            hours, minutes, seconds = int(hours), int(minutes), int(seconds)
        return datetime(year, month, day, hours, minutes, seconds, micro)


    @staticmethod
    def to_str(value):
        if value is None:
            return ''
        micro = value.microsecond
        if micro:
            return value.strftime('%Y-%m-%d %H:%M:%S.%d' % micro)
        return value.strftime('%Y-%m-%d %H:%M:%S')



# data types for each property
# --> TO VERIFY AND COMPLETE
# occurs = 0  means 0..n occurrences
data_properties = {
  'BEGIN': Unicode(occurs=1),
  'END': Unicode(occurs=1),
  'VERSION': Unicode(occurs=1),
  'PRODID': Unicode(occurs=1),
  'METHOD': Unicode(occurs=1),
  # Component properties
  'ATTACH': URI(occurs=0),
  'CATEGORY': Unicode(occurs=1),
  'CATEGORIES': Unicode(occurs=0),
  'CLASS': Unicode(occurs=1),
  'COMMENT': Unicode(occurs=0),
  'DESCRIPTION': Unicode(occurs=1),
  'GEO': Unicode(occurs=1),
  'LOCATION': Unicode(occurs=1),
  'PERCENT-COMPLETE': Integer(occurs=1),
  'PRIORITY': Integer(occurs=1),
  'RESOURCES': Unicode(occurs=0),
  'STATUS': Unicode(occurs=1),
  'SUMMARY': Unicode(occurs=1),
  # Date & Time component properties
  'COMPLETED': DateTime(occurs=1),
  'DTEND': DateTime(occurs=1),
  'DUE': DateTime(occurs=1),
  'DTSTART': DateTime(occurs=1),
  'DURATION': Unicode(occurs=1),
  'FREEBUSY': Unicode(occurs=1),
  'TRANSP': Unicode(occurs=1),
  # Time Zone component properties
  'TZID': Unicode(occurs=1),
  'TZNAME': Unicode(occurs=0),
  'TZOFFSETFROM': Unicode(occurs=1),
  'TZOFFSETTO': Unicode(occurs=1),
  'TZURL': URI(occurs=1),
  # Relationship component properties
  'ATTENDEE': URI(occurs=0),
  'CONTACT': Unicode(occurs=0),
  'ORGANIZER': URI(occurs=1),
  # Recurrence component properties
  'EXDATE': DateTime(occurs=0),
  'EXRULE': Unicode(occurs=0),
  'RDATE': Unicode(occurs=0),
  'RRULE': Unicode(occurs=0),
  # Alarm component properties
  'ACTION': Unicode(occurs=1),
  'REPEAT': Integer(occurs=1),
  'TRIGGER': Unicode(occurs=1),
  # Change management component properties
  'CREATED': DateTime(occurs=1),
  'DTSTAMP': DateTime(occurs=1),
  'LAST-MODIFIED': DateTime(occurs=1),
  'SEQUENCE': Integer(occurs=1),
  # Others
  'RECURRENCE-ID': DateTime(occurs=1),
  'RELATED-TO': Unicode(occurs=1),
  'URL': URI(occurs=1),
  'UID': String(occurs=1)
}

################################################################
#                         NOT USED ACTUALLY
#statvalue = {'VEVENT': ['TENTATIVE', 'CONFIRMED', 'CANCELLED']}
#classvalue = ['PRIVATE', 'PUBLIC', 'CONFIDENTIAL']
################################################################

###################################################################
# Manage an icalendar content line property :
#
#   name *(;param-name=param-value1[, param-value2, ...]) : value CRLF
#
#
# Parse the property line separating as :
#
#   property name  >  name
#   value & parameter list > property_value
#
#   XXX test if the property accepts the given parameters
#       could be a great idea but could be done on Component
#
###################################################################

