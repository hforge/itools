# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from httplib import HTTPConnection
from urllib import urlopen

# Import from itools
from itools.vfs import BaseFS, register_file_system
from headers import HTTPDate


class HTTPFS(BaseFS):

    @staticmethod
    def _head(reference):
        conn = HTTPConnection(str(reference.authority))
        # XXX Add the query
        conn.request('HEAD', str(reference.path))
        return conn.getresponse()


    @staticmethod
    def exists(reference):
        response = HTTPFS._head(reference)
        status = int(response.status)
        return status < 400 or status >= 500


    @staticmethod
    def is_file(reference):
        return HTTPFS.exists(reference)


    @staticmethod
    def is_folder(reference):
        return False


    @staticmethod
    def get_mtime(reference):
        response = HTTPFS._head(reference)
        mtime = response.getheader('last-modified')
        if mtime is None:
            return None
        return HTTPDate.decode(mtime)


    @classmethod
    def get_mimetype(cls, reference):
        response = HTTPFS._head(reference)
        ctype = response.getheader('content-type')
        return ctype.split(';')[0]


    @staticmethod
    def open(reference, mode=None):
        reference = str(reference)
        return urlopen(reference) 


register_file_system('http', HTTPFS)
