# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.datatypes import (Unicode, String, ISODateTime, ISOCalendarDate,
                              ISOTime)
from base import Schema
import registry


# XXX Backwards compatibility, an upgrade method needed in itools.cms to
# update the dates
class DateTime(ISODateTime):

    @staticmethod
    def decode(value):
        if not value:
            return None
        if ' ' in value:
            date, time = value.split()
        else:
            date, time = value.split('T')
        date = ISOCalendarDate.decode(date)
        time = ISOTime.decode(time)

        return datetime.combine(date, time)



class DublinCore(Schema):

    class_uri = 'http://purl.org/dc/elements/1.1/'
    class_prefix = 'dc'


    datatypes = {'contributor': None,
                 'coverage': None,
                 'creator': String,
                 'date': DateTime,
                 'description': Unicode,
                 'format': None,
                 'identifier': String,
                 'language': String,
                 'publisher': Unicode,
                 'relation': None,
                 'rights': None,
                 'source': None,
                 'subject': None,
                 'title': Unicode,
                 'type': None,
                 }


registry.register_schema(DublinCore)
# XXX For backwards compatibility, introduced in 0.15.1
registry.register_schema(DublinCore, uri='http://purl.org/dc/elements/1.1')
