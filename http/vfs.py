# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
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
from httplib import HTTPConnection, FOUND
from urllib import urlopen

# Import from itools
from itools.vfs import BaseFS, register_file_system
from itools.datatypes import HTTPDate
from itools.uri import get_reference


class HTTPFS(BaseFS):

    @staticmethod
    def _head(reference, nredirects=20):
        conn = HTTPConnection(str(reference.authority))
        # FIXME Add the query
        conn.request('HEAD', str(reference.path))
        response = conn.getresponse()
        # Follow the redirection
        if response.status == FOUND and nredirects > 0:
            location = response.getheader('location')
            location = get_reference(location)
            return HTTPFS._head(location, nredirects - 1)

        return response


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


    @classmethod
    def get_size(cls, reference):
        response = HTTPFS._head(reference)
        size = response.getheader('content-length')
        if size is None:
            return 0
        return long(size)


    @staticmethod
    def open(reference, mode=None):
        # TODO Check whether 'urlopen' has a redirection limit
        reference = str(reference)
        return urlopen(reference)


register_file_system('http', HTTPFS)
