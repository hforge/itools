# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# XXX Test with windows, maybe we will have to use os.'path.join'

# Import from the Standard Library
import datetime
import mimetypes
import os
import time

# Import from itools
from itools import uri
import base


class Resource(base.Resource):

    def __init__(self, uri_reference):
        base.Resource.__init__(self, uri_reference)
        # Keep a copy of the path as a plain string, because this is what
        # the 'os.*' and 'os.path.*' expects. Used internally.
        self._path = str(self.uri.path)


    def get_atime(self):
        """Returns the last time the resource was accessed."""
        if not os.path.exists(self._path):
            return None
        time = os.path.getatime(self._path)
        return datetime.datetime.fromtimestamp(time)


    def get_mtime(self):
        """Returns the last time the resource was modified."""
        if not os.path.exists(self._path):
            return None
        time = os.path.getmtime(self._path)
        return datetime.datetime.fromtimestamp(time)


    def get_ctime(self):
        """Returns the time the resource was created."""
        if not os.path.exists(self._path):
            return None
        time = os.path.getctime(self._path)
        return datetime.datetime.fromtimestamp(time)


    def set_mtime(self, mtime):
        atime = os.path.getatime(self._path)
        mtime = time.mktime(mtime.timetuple())
        os.utime(self._path, (atime, mtime))



class File(Resource, base.File):

    _file = None

    def open(self):
        try:
            self._file = open(self._path, 'r+b')
        except IOError:
            self._file = open(self._path, 'rb')


    def close(self):
        self._file.close()
        self._file = None


    def is_open(self):
        return self._file is not None


    def seek(self, offset, whence=0):
        self._file.seek(offset, whence)


    def read(self, size=-1):
        return self._file.read(size)


    def readline(self):
        return self._file.readline()


    def write(self, data):
        self._file.write(data)


    def truncate(self, size=None):
        if size is None:
            self._file.truncate()
        else:
            self._file.truncate(size)


    def get_size(self):
        return os.path.getsize(self._path)



class Folder(Resource, base.Folder):

    def _get_resource_names(self):
        return os.listdir(self._path)


    def _get_resource(self, name):
        reference = self.uri.resolve(name)
        return get_resource(reference)


    def _has_resource(self, name):
        path = '%s/%s' % (self._path, name)
        return os.path.exists(path)


    def _set_file_resource(self, name, resource):
        data = resource.read()
        file('%s/%s' % (self._path, name), 'wb').write(data)


    def _set_folder_resource(self, name, resource):
        os.mkdir('%s/%s' % (self._path, name))


    def _del_file_resource(self, name):
        os.remove('%s/%s' % (self._path, name))


    def _del_folder_resource(self, name):
        os.rmdir('%s/%s' % (self._path, name))



def get_resource(reference):
    path = str(reference.path)
    if os.path.isfile(path):
        return File(reference)
    elif os.path.isdir(path):
        if not str(reference).endswith('/'):
            reference = uri.generic.decode(str(reference) + '/')
        return Folder(reference)
    raise IOError, 'nor file neither folder at %s' % reference
