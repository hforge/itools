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
from datetime import datetime
import thread

# Import from itools
from itools import uri
import base
from itools.web import get_context

# Import from Zope
from Acquisition import aq_base
from OFS.Image import File as ZopeFile
from OFS.Folder import Folder as ZopeFolder
from AccessControl import User
import webdav
import Zope2


# Zope is not an scheme, this means Zope resources only can be accessible
# within a context.
roots = {}
roots_lock = thread.allocate_lock()


def get_object(path):
    """
    Returns the Zope object in the given path.
    """
    # Get the root
    key = thread.get_ident()
    if key in roots:
        root = roots[key]
    else:
        root = Zope2.DB.open().root()['Application']
        root = aq_base(root)
        roots_lock.acquire()
        try:
            roots[key] = root
        finally:
            roots_lock.release()

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
        return lock, key


    def unlock(self, key):
        object = self._get_object()
        key = webdav.common.tokenFinder(key)
        object.wl_delLock(key)


    def is_locked(self):
        # XXX Implement! See Zope's "webdav.Resource.LOCK".
        raise NotImplementedError


    ##########################################################################
    # Transactions
    ##########################################################################
    def start_transaction(self):
        get_transaction().begin()


    def abort_transaction(self):
        get_transaction().abort()


    def commit_transaction(self):
        get_transaction().commit()



class File(Resource, base.File):

    def get_mimetype(self):
        object = self._get_object()
        return object.content_type


    def read(self):
        object = self._get_object()
        return str(object.data)


    def write(self, data):
        object = self._get_object()
        object.update_data(data)


    def __setitem__(self, index, value):
        object = self._get_object()
        data = str(object.data)

        if isinstance(index, slice):
            # XXX So far 'step' is not supported
            start, stop = index.start, index.stop
        else:
            start, stop = index, index + 1
        data = data[:start] + value + data[stop:]
        object.update_data(data)



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
