# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
# Copyright (C) 2010-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
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
# Fixed offset
###########################################################################

# FIXME pytz imports gettext, if we import pytz early then 'setup.py install'
# fails because pytz imports itools.gettext by mistake.
# TODO Rename itools.gettext to something else? That would allow to simplify
# the code below

FixedOffset = None
utc = None

def _init():
    global FixedOffset
    if FixedOffset is None:
        from pytz import _FixedOffset
        class FixedOffset(_FixedOffset):
            def tzname(self, dt):
                minutes = self._minutes
                sign = '-' if minutes < 0 else '+'
                minutes = abs(minutes)
                return '%s%02d:%02d' % (sign, minutes/60, minutes%60)

    global utc
    if utc is None:
        from pytz import UTC as _UTC
        class UTC(_UTC.__class__):
            def tzname(self, dt):
                return "Z"
        utc = UTC()


def fixed_offset(offset, _tzinfos={}):
    """Returns a pytz compatible fixed-offset timezone. The given offset
    is in minutes.
    """
    # Cache
    tz = _tzinfos.get(offset)
    if tz:
        return tz

    # Initialize global variables (XXX see comments above)
    _init()

    # Ok
    tz = utc if offset == 0 else FixedOffset(offset)
    _tzinfos[offset] = tz
    return tz


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
