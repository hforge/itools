# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from httplib import HTTPConnection
from urllib import urlopen

# Import from itools
from itools.vfs.base import BaseFS
from itools.vfs.registry import register_file_system


class HTTPFS(BaseFS):
    

    @staticmethod
    def exists(reference):
        conn = HTTPConnection(str(reference.authority))
        # XXX Add the query
        conn.request('HEAD', str(reference.path))
        response = conn.getresponse()
        status = int(response.status)
        return status < 400 or status >= 500


    @staticmethod
    def is_file(reference):
        return HTTPFS.exists(reference)


    @staticmethod
    def is_folder(reference):
        return False


    @staticmethod
    def open(reference):
        reference = str(reference)
        return urlopen(reference) 


register_file_system('http', HTTPFS)
