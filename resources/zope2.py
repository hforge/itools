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

# Import from itools
from itools import uri
import base
from itools.zope import get_context

# Import from Zope
from OFS.Image import File as ZopeFile
from OFS.Folder import Folder as ZopeFolder
from AccessControl import User
import webdav



# XXX
#
# Zope 2 resources should use "bobobase_modification_time()", so if a
# resource is modified through the ZMI (for example) the resource is
# reloaded the next time.
#
# But unfortunately we can't use it.
#
# Because the "bobobase_modification_time" is set with the ZODB transaction
# commit, which happens always at the end, after the handler timestamp has
# been set. This means that the resource modification time is always newer
# than the handler's timestamp; so the resource always would be reloaded
# after a modification, what is unacceptable.
#
# This is the reason we keep ourselves the modification time, within the
# persistent variable 'mtime'. When the resource is loaded for the first
# time the on memory variable "bobo_time" is initialized; the modification
# time of a resource is defined as the newer of the "object.mtime" and
# "resource.bobo_time" variables.


class Resource(base.Resource):

    uri = None

    def __init__(self, uri_reference):
        base.Resource.__init__(self, uri_reference)
        # Keep a copy of the path as a plain string, because this is what
        # the 'os.*' and 'os.path.*' expects. Used internally.
        self._path = str(self.uri.path)
        # Initialize the modification time with the "bobase modification time"
        object = self._get_object()
        bobo_time = object.bobobase_modification_time()
        bobo_time = bobo_time.timeTime()
        self.bobo_time = datetime.fromtimestamp(bobo_time)


    def _get_object(self):
        root = get_context().request.zope_request['PARENTS'][-1]
        return root.unrestrictedTraverse(self._path).aq_base


    def get_atime(self):
        return None


    def get_mtime(self):
        object = self._get_object()
        mtime = getattr(object, 'mtime', None)

        if mtime is None or mtime < self.bobo_time:
            return self.bobo_time
        return mtime


    def get_ctime(self):
        return None


    def set_mtime(self, mtime):
        raise NotImplementedError


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



class File(Resource, base.File):

    def get_mimetype(self):
        object = self._get_object()
        return object.content_type


    def get_data(self):
        object = self._get_object()
        return str(object.data)


    def set_data(self, data):
        object = self._get_object()
        object.update_data(data)
        # Set modification time
        object.mtime = datetime.now()


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
        # Set modification time
        object.mtime = datetime.now()



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
        object._setObject(name, ZopeFile(name, '', resource.get_data()))
        # Set modification time
        object.mtime = datetime.now()


    def _set_folder_resource(self, name, resource):
        object = self._get_object()
        object._setObject(name, ZopeFolder(name))
        # Set modification time
        object.mtime = datetime.now()


    def _del_file_resource(self, name):
        object = self._get_object()
        object._delObject(name)
        # Set modification time
        object.mtime = datetime.now()


    def _del_folder_resource(self, name):
        object = self._get_object()
        object._delObject(name)
        # Set modification time
        object.mtime = datetime.now()



def get_resource(reference):
    # Get path
    if isinstance(reference, uri.Reference):
        path = str(reference.path)
    elif isinstance(reference, uri.Path):
        path = str(reference)
    else:
        path = reference
    # Get object
    root = get_context().request.zope_request['PARENTS'][-1]
    object = root.unrestrictedTraverse(path)
    # Return resource
    if object.meta_type == 'File':
        return File(reference)
    elif object.meta_type == 'Folder':
        return Folder(reference)
    else:
        raise IOError, 'nor file neither folder at %s' % reference
