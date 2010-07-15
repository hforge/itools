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


class UTC(tzinfo):

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "Z"

    def dst(self, dt):
        return timedelta(0)

# A class capturing the platform's idea of local time.
# Paste from Python datetime doc

STDOFFSET = timedelta(seconds = -timezone)
if daylight:
    DSTOFFSET = timedelta(seconds = -altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET

class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        stamp = mktime(tt)
        tt = localtime(stamp)
        return tt.tm_isdst > 0

utc = UTC()
local_tz = LocalTimezone()
