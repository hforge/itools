# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import thread
import weakref

# Import from itools
from itools.uri.generic import Path
import base

# Import from the ZODB
from persistent import Persistent
from BTrees.OOBTree import OOBTree
import ZODB



class DataBase(object):

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
        elif isinstance(object, str):
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
                raise LookupError, 'object "%s" not found' % str(path)

        return object


    #######################################################################
    # API
    #######################################################################
    def get_name(self):
        return self.path[-1]

    name = property(get_name, None, None, '')


##    def get_ctime(self):
##        return self.ctime


##    def get_mtime(self):
##        return self.mtime


##    def get_atime(self):
##        # XXX Should we correctly keep the real access time??
##        return self.mtime


##    def set_mtime(self, mtime):
##        self.mtime = mtime



class File(Resource, base.File):

    def _get_parent(self):
        connection = self.connection()
        object = connection.root()
        for segment in self.path[:-1]:
            try:
                object = object[segment.name]
            except KeyError:
                raise LookupError, 'object "%s" not found' % str(path)

        return object


    def read(self):
        return self._get_object()


    def write(self, data):
        parent = self._get_parent()
        parent[self.name] = data


    def __setitem__(self, index, value):
        # Read
        data = self._get_object()
        # Modify
        if isinstance(index, slice):
            # XXX So far 'step' is not supported
            start, stop = index.start, index.stop
        else:
            start, stop = index, index + 1
        data = data[:start] + value + data[stop:]
        # Write
        self.write(data)



class Folder(Resource, base.Folder):

    def _get_resource_names(self):
        object = self._get_object()
        return object.keys()


    def _get_resource(self, name):
        object = self._get_object()
        object = object[name]

        path = Path('%s/%s' % (self.path, name))
        if isinstance(object, OOBTree):
            return Folder(self.connection(), path)
        elif isinstance(object, str):
            return File(self.connection(), path)

        raise IOError, 'nor file neither folder at %s' % path


    def _has_resource(self, name):
        object = self._get_object()
        return name in object


    def _set_file_resource(self, name, resource):
        object = self._get_object()
        object[name] = resource.read()


    def _set_folder_resource(self, name, resource):
        object = self._get_object()
        object[name] = OOBTree()


    def _del_file_resource(self, name):
        object = self._get_object()
        del object[name]


    def _del_folder_resource(self, name):
        object = self._get_object()
        del object[name]
