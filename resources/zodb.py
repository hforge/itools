# -*- coding: ISO-8859-1 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from datetime import datetime
from random import random
import thread
from time import time
import weakref

# Import from itools
from itools.uri.generic import Path
import base

# Import from the ZODB
from BTrees.OOBTree import OOBTree
import transaction
import ZODB



class Database(object):

    def __init__(self, storage):
        self.database = ZODB.DB(storage)
        self.connections = {}
        self.lock = thread.allocate_lock()


    def get_resource(self, path):
        # Pre-process input data
        if isinstance(path, str):
            path = Path(path)

        # Get the connection
        ident = thread.get_ident()
        if ident in self.connections:
            connection = self.connections[ident]
        else:
            connection = self.database.open()
            self.lock.acquire()
            try:
                self.connections[ident] = connection
            finally:
                self.lock.release()

        # Check for the root object
        if not path:
            return Folder(connection, path)

        # Find the database object
        object = connection.root()
        for segment in path:
            try:
                object = object[segment.name]
            except KeyError:
                raise LookupError, 'object "%s" not found' % str(path)

        # Build and return the resource
        if isinstance(object, OOBTree):
            return Folder(connection, path)
        elif isinstance(object, tuple):
            return File(connection, path)

        # Unexpected object
        raise IOError, 'nor file neither folder at %s' % path



class Resource(base.Resource):

    def __init__(self, connection, path):
        self.connection = weakref.ref(connection)
        self.path = path


    def _get_object(self):
        connection = self.connection()
        object = connection.root()
        for segment in self.path:
            try:
                object = object[segment.name]
            except KeyError:
                raise LookupError, 'object "%s" not found' % str(self.path)

        return object


    #######################################################################
    # API
    #######################################################################
    def get_name(self):
        return self.path[-1].name

    name = property(get_name, None, None, '')


    def get_ctime(self):
        return None


    def get_atime(self):
        return None


##    def set_mtime(self, mtime):
##        self.mtime = mtime


    def get_transaction(self):
        return transaction.get()



class File(Resource, base.File):

    offset = 0


    def _get_parent(self):
        connection = self.connection()
        object = connection.root()
        for segment in self.path[:-1]:
            try:
                object = object[segment.name]
            except KeyError:
                raise LookupError, 'object "%s" not found' % str(self.path)

        return object


    def get_mtime(self):
        mtime, data, lock = self._get_object()
        return mtime


    def get_size(self):
        mtime, data, lock = self._get_object()
        return len(data)


    def open(self):
        self.offset = 0


    def close(self):
        self.offset = 0


    def is_open(self):
        return True


    def seek(self, offset, whence=0):
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.get_size() + offset
        else:
            message = 'unsupported value "%s" for "whence" parameter' % whence
            raise ValueError, message


    def read(self, size=None):
        mtime, data, lock = self._get_object()
        if size is None:
            data = data[self.offset:]
        else:
            data = data[self.offset:self.offset+size]
        self.offset += len(data)
        return data


    def readline(self):
        mtime, data, lock = self._get_object()
        end = data.find('\n', self.offset)
        if end == -1:
            data = data[self.offset:]
        else:
            data = data[self.offset:end+1]
        self.offset += len(data)
        return data


    def write(self, data):
        parent = self._get_parent()
        mtime, old_data, lock = parent[self.name]

        old_offset = self.offset
        self.offset += len(data)
        data = old_data[:old_offset] + data + old_data[self.offset:]
        parent[self.name] = (datetime.now(), data, lock)


    def truncate(self, size=None):
        if size is None:
            size = self.offset

        parent = self._get_parent()
        mtime, data, lock = parent[self.name]

        parent[self.name] = (datetime.now(), data[:size], lock)


    def __setitem__(self, index, value):
        # Read
        parent = self._get_parent()
        mtime, data, lock = parent[self.name]
        # Write
        data = data[:index] + value + data[index+1:]
        parent[self.name] = (datetime.now(), data, lock)
        self.offset += 1


    def __setslice__(self, start, stop, value):
        # Read
        parent = self._get_parent()
        mtime, data, lock = parent[self.name]
        # Write
        data = data[:start] + value + data[stop:]
        parent[self.name] = (datetime.now(), data, lock)
        self.offset = stop



class Folder(Resource, base.Folder):

    def get_mtime(self):
        object = self._get_object()
        mtime = object._p_mtime
        if mtime is None:
            return datetime.now()
        return datetime.fromtimestamp(mtime)


    def _get_names(self):
        object = self._get_object()
        return object.keys()


    def _get_resource(self, name):
        object = self._get_object()
        object = object[name]

        path = Path('%s/%s' % (self.path, name))
        if isinstance(object, OOBTree):
            return Folder(self.connection(), path)
        elif isinstance(object, tuple):
            return File(self.connection(), path)

        raise IOError, 'nor file neither folder at %s' % path


    def _has_resource(self, name):
        object = self._get_object()
        return name in object


    def _set_file_resource(self, name, resource):
        object = self._get_object()
        object[name] = (datetime.now(), resource.read(), None)


    def _set_folder_resource(self, name, resource):
        object = self._get_object()
        object[name] = OOBTree()


    def _del_file_resource(self, name):
        object = self._get_object()
        del object[name]


    def _del_folder_resource(self, name):
        object = self._get_object()
        del object[name]
