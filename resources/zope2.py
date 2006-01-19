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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from datetime import datetime
import thread

# Import from itools
from itools import uri
import base

# Import from Zope
from Acquisition import aq_base
from OFS.Image import File as ZopeFile
from OFS.Folder import Folder as ZopeFolder
from AccessControl import User
import transaction
import webdav
import Zope2


# Zope is not an scheme, this means Zope resources only can be accessible
# within a context.
connections = {}
connections_lock = thread.allocate_lock()


def get_object(path):
    """
    Returns the Zope object in the given path.
    """
    database = Zope2.DB
    database_name = database.getName()

    if database_name in connections:
        connection = connections[database_name]
    else:
        connections_lock.acquire()
        try:
            connection = database.open()
            connections[database_name] = connection
        finally:
            connections_lock.release()

    root = connection.root()['Application']
    root = aq_base(root)

    # Traverse
    object = root
    for segment in path:
        try:
            object = getattr(object, segment.name)
        except AttributeError:
            raise LookupError, 'object "%s" not found' % str(path)

    return object



class Resource(base.Resource):

    uri = None

    def __init__(self, uri_reference):
        base.Resource.__init__(self, uri_reference)
        # Keep a copy of the path as a plain string, because this is what
        # the 'os.*' and 'os.path.*' expects. Used internally.
        self._path = self.uri.path


    def _get_object(self):
        return get_object(self._path)


    def get_atime(self):
        return None


    def get_mtime(self):
        object = self._get_object()
        mtime = object.bobobase_modification_time().timeTime()
        return datetime.fromtimestamp(mtime)


    def get_ctime(self):
        return None


    def set_mtime(self, mtime):
        raise NotImplementedError


    ##########################################################################
    # Locking (prevent other threads to touch the resource)
    ##########################################################################
    def lock(self):
        object = self._get_object()
        creator = User.nobody
        lock = webdav.LockItem.LockItem(creator)
        key = lock.getLockToken()
        object.wl_setLock(key, lock)
        return key


    def unlock(self, key):
        object = self._get_object()
        key = webdav.common.tokenFinder(key)
        object.wl_delLock(key)


    def is_locked(self):
        object = self._get_object()
        return object.wl_isLocked()


    ##########################################################################
    # Transactions
    ##########################################################################
    def get_transaction(self):
        return transaction.get()



class File(Resource, base.File):

    offset = 0


    def get_mimetype(self):
        object = self._get_object()
        return object.content_type


    def get_size(self):
        object = self._get_object()
        data = str(object.data)
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
        object = self._get_object()
        data = str(object.data)
        if size is None:
            data = data[self.offset:]
        else:
            data = data[self.offset:self.offset+size]
        self.offset += len(data)
        return data


    def readline(self):
        object = self._get_object()
        data = str(object.data)
        end = data.find('\n', self.offset)
        if end == -1:
            data = data[self.offset:]
        else:
            data = data[self.offset:end+1]
        self.offset += len(data)
        return data


    def write(self, data):
        object = self._get_object()
        old_data = str(object.data)
        old_offset = self.offset
        self.offset += len(data)
        data = old_data[:old_offset] + data + old_data[self.offset:]
        object.update_data(data)


    def truncate(self, size=None):
        if size is None:
            size = self.offset

        object = self._get_object()
        data = str(object.data)

        object.update_data(data[:size])


    def __setitem__(self, index, value):
        # Read
        object = self._get_object()
        data = str(object.data)
        # Write
        data = data[:index] + value + data[index+1:]
        object.update_data(data)
        self.offset += 1


    def __setslice__(self, start, stop, value):
        # Read
        object = self._get_object()
        data = str(object.data)
        # Write
        data = data[:start] + value + data[stop:]
        object.update_data(data)
        self.offset = stop



class Folder(Resource, base.Folder):

    def _get_resource_names(self):
        object = self._get_object()
        return object.objectIds()


    def _get_resource(self, name):
        reference = self.uri.path.resolve2(name)
        return get_resource(reference)


    def _has_resource(self, name):
        return name in self._get_resource_names()


    def _set_file_resource(self, name, resource):
        object = self._get_object()
        object._setObject(name, ZopeFile(name, '', resource.read()))


    def _set_folder_resource(self, name, resource):
        object = self._get_object()
        object._setObject(name, ZopeFolder(name))


    def _del_file_resource(self, name):
        object = self._get_object()
        object._delObject(name)


    def _del_folder_resource(self, name):
        object = self._get_object()
        object._delObject(name)


def get_resource(path):
    """
    Returns the resource at the given path.
    """
    # Check the type
    if not isinstance(path, uri.Path):
        path = uri.Path(path)

    # Get the object
    object = get_object(path)

    # Check type
    if object.meta_type == 'File':
        return File(path)
    elif object.meta_type == 'Folder':
        return Folder(path)

    raise IOError, 'nor file neither folder at "%s"' % path
