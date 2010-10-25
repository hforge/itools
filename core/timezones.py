# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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
from datetime import timedelta, tzinfo
from time import altzone, daylight, localtime, mktime, timezone, tzname


###########################################################################
# UTC
###########################################################################
class UTC(tzinfo):

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        # pytz.utc returns 'UTC', otherwise we could use it
        return "Z"

    def dst(self, dt):
        return timedelta(0)

utc = UTC()


###########################################################################
# Local Time (copied from from Python datetime doc)
###########################################################################
ZERO = timedelta(0)
STDOFFSET = timedelta(seconds = -timezone)
DSTOFFSET = timedelta(seconds = -altzone) if daylight else STDOFFSET
DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        return DSTOFFSET if self._isdst(dt) else STDOFFSET


    def dst(self, dt):
        return DSTDIFF if self._isdst(dt) else ZERO


    def tzname(self, dt):
        return tzname[self._isdst(dt)]


    def _isdst(self, dt):
        stamp = mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute,
                        dt.second, dt.weekday(), 0, -1))
        tt = localtime(stamp)
        return tt.tm_isdst > 0


    def localize(self, dt, is_dst=False):
        """Implemented for compatibility with pytz
        """
        if dt.tzinfo is not None:
            raise ValueError, 'Not naive datetime (tzinfo is already set)'
        return dt.replace(tzinfo=self)


local_tz = LocalTimezone()
