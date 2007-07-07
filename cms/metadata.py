# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import base64
import urllib
from datetime import time

# Import from itools
from itools.datatypes import DataType, Boolean, Email, String, Tokens, Unicode
from itools.schemas import Schema as BaseSchema, get_datatype, register_schema



class Password(DataType):

    @staticmethod
    def decode(data):
        data = urllib.unquote(data)
        return base64.decodestring(data)


    @staticmethod
    def encode(value):
        value = base64.encodestring(value)
        return urllib.quote(value)



class Record(object):

    default = []



class Timetables(DataType):
    """
    Timetables are tuples of time objects (start, end) used by cms.ical.

    Example with 3 timetables as saved into metadata:
        (8,0),(10,0);(10,0),(12,0);(15,30),(17,30)

    Decoded value are:
        [(time(8,0), time(10,0)), (time(10,0), time(12, 0)),
         (time(15,30), time(17, 30))]
    """
    @staticmethod
    def decode(value):
        if not value:
            return ()
        timetables = []
        for timetable in value.strip().split(';'):
            start, end = timetable[1:-1].split('),(')
            hours, minutes = start.split(',')
            hours, minutes = int(hours), int(minutes)
            start = time(hours, minutes)
            hours, minutes = end.split(',')
            hours, minutes = int(hours), int(minutes)
            end = time(hours, minutes)
            timetables.append((start, end))
        return tuple(timetables)


    @staticmethod
    def encode(value):
        timetables = []
        for start, end in value:
            start = '(' + str(start.hour) + ',' + str(start.minute) + ')'
            end = '(' + str(end.hour) + ',' + str(end.minute) + ')'
            timetables.append(start + ',' + end)
        return ';'.join(timetables)



class Schema(BaseSchema):

    class_uri = 'http://xml.ikaaro.org/namespaces/metadata'
    class_prefix = 'ikaaro'


    datatypes = {
##        'format': String,
##        'version': String,
##        'owner': String,
        # Workflow
        'wf_transition': Record,
##        'name': String,
##        'user': String,
##        'comments': Unicode,
        # History
        'history': Record,
        # Users
        'firstname': Unicode,
        'lastname': Unicode,
        'email': Email,
        'password': Password,
        'user_theme': String(default='aruni'), # XXX unused
        'user_language': String(default='en'),
        'website_is_open': Boolean(default=False),
        'website_languages': Tokens(default=('en',)),
        'user_must_confirm': String,
        # Backwards compatibility
        'username': String,
        # Future
        'order': Tokens(default=()),
        # Roles
        'admins': Tokens(default=()),
        'guests': Tokens(default=()),
        'members': Tokens(default=()),
        'reviewers': Tokens(default=()),
        # Settings
        'contacts': Tokens(default=()),
        # ical
        'timetables': Timetables,
        }


register_schema(Schema)

