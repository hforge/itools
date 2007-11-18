# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.datatypes import (Unicode, String, ISODateTime, ISOCalendarDate,
                              ISOTime)
from base import BaseSchema
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



class DublinCore(BaseSchema):

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
                 'subject': Unicode,
                 'title': Unicode,
                 'type': None,
                 }


# XXX For backwards compatibility, register the schema also with the old
# and wrong uri (introduced in 0.15.1)
registry.register_schema(DublinCore, 'http://purl.org/dc/elements/1.1')
