# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.core import freeze
from itools.datatypes import DataType, Integer, ISOTime , URI, Unicode, String


class Time(ISOTime):
    """This datatype is the same as ISOTime except that its encode method
    don't use seconds if not explicitely notified.
    """
    @staticmethod
    def encode(value, seconds=False):
        if value is None:
            return ''
        if not seconds:
            return value.strftime('%H:%M')
        return value.strftime('%H:%M:%S')



class DateTime(DataType):
    """iCalendar Date format:

    DTSTART:19970714T133000.000000 (local time)

    DTSTART:19970714T173000Z (UTC time)

    DTSTART;TZID=US-Eastern:19970714T133000 (local time + timezone)
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
record_properties = freeze({
  'BEGIN': String(multiple=False),
  'END': String(multiple=False),
  'VERSION': Unicode(multiple=False),
  'PRODID': Unicode(multiple=False),
  'METHOD': Unicode(multiple=False),
  # Component properties
  'ATTACH': URI(multiple=True),
  'CATEGORY': Unicode(multiple=False),
  'CATEGORIES': Unicode(multiple=True),
  'CLASS': Unicode(multiple=False),
  'COMMENT': Unicode(multiple=True),
  'DESCRIPTION': Unicode(multiple=False),
  'GEO': Unicode(multiple=False),
  'LOCATION': Unicode(multiple=False),
  'PERCENT-COMPLETE': Integer(multiple=False),
  'PRIORITY': Integer(multiple=False),
  'RESOURCES': Unicode(multiple=True),
  'STATUS': Unicode(multiple=False),
  'SUMMARY': Unicode(multiple=False, indexed=True, mandatory=True),
  # Date & Time component properties
  'COMPLETED': DateTime(multiple=False),
  'DTEND': DateTime(multiple=False, stored=True, indexed=True),
  'DUE': DateTime(multiple=False),
  'DTSTART': DateTime(multiple=False, stored=True, indexed=True),
  'DURATION': Unicode(multiple=False),
  'FREEBUSY': Unicode(multiple=False),
  'TRANSP': Unicode(multiple=False),
  # Time Zone component properties
  'TZID': Unicode(multiple=False),
  'TZNAME': Unicode(multiple=True),
  'TZOFFSETFROM': Unicode(multiple=False),
  'TZOFFSETTO': Unicode(multiple=False),
  'TZURL': URI(multiple=False),
  # Relationship component properties
  'ATTENDEE': URI(multiple=True),
  'CONTACT': Unicode(multiple=True),
  'ORGANIZER': URI(multiple=False),
  # Recurrence component properties
  'EXDATE': DateTime(multiple=True),
  'EXRULE': Unicode(multiple=True),
  'RDATE': Unicode(multiple=True),
  'RRULE': Unicode(multiple=True),
  # Alarm component properties
  'ACTION': Unicode(multiple=False),
  'REPEAT': Integer(multiple=False),
  'TRIGGER': Unicode(multiple=False),
  # Change management component properties
  'CREATED': DateTime(multiple=False),
  'DTSTAMP': DateTime(multiple=False),
  'LAST-MODIFIED': DateTime(multiple=False),
  'SEQUENCE': Integer(multiple=False),
  # Others
  'RECURRENCE-ID': DateTime(multiple=False),
  'RELATED-TO': Unicode(multiple=False),
  'URL': URI(multiple=False),
  'UID': String(multiple=False, indexed=True)
})



record_parameters = freeze({
    'ALTREP': URI(multiple=False),
    # TODO Finish the list
})



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

