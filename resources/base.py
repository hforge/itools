# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from Python
from types import StringTypes

# Import from itools
from itools import uri


class Resource:
    """
    There are two types of resources, files and folders. The generic API for
    them is:

    - get_atime(): returns the last time the object was accessed

    - get_mtime(): returns the last time the object was modified

    - get_ctime(): returns the time the object was created

    - get_mimetype(): returns the mime type of the resource (None means it
        is unknown)

    Note that resources are classic Python objects, this is because we want
    to support the ZODB 3.2, which is based on old extension classes, which
    are incompatible with new style Python classes. This will change when
    ZODB 3.3 and Zope 2.8 arrive (XXX).
    """

    def __init__(self, uri_reference):
        self.uri_reference = uri_reference


    def get_mimetype(self):
        return ''




class File(Resource):
    def __str__(self):
        raise NotImplementedError


    def __getitem__(self, index):
        return str(self)[index]


    def __setitem__(self, index, value):
        raise NotImplementedError


    def __getslice__(self, a, b):
        return str(self)[a:b]


    def set_data(self, data):
        raise NotImplementedError


    def get_size(self):
        return len(str(self))


    def get_data(self):
        # XXX Kept here for backwards compatibility only
        return str(self)



class Folder(Resource):

    def get_mimetype(self):
        return 'application/x-not-regular-file'


    ######################################################################
    # Specific folder API
    def get_resources(self, path='.'):
        resource = self.get_resource(path)
        return resource._get_resources()


    def get_resource(self, path):
        """
        Returns the required resource, or None if it does not exists.
        """
        # Normalize the path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        # Special case: '.'
        if len(path) == 0:
            return self

        # Traverse the path
        resource = self
        for i, segment in enumerate(path):
            resource = resource._get_resource(segment.name)
            if resource is None:
                raise LookupError, "resource '%s' not found" % str(path[:i+1])
        return resource


    def has_resource(self, path):
        # Normalize and split the path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        # Traverse
        folder = self
        for segment in path[:-1]:
            folder = folder._get_resource(segment.name)

        segment = path[-1]
        return folder._has_resource(segment.name)


    def set_resource(self, path, resource):
        # Normalize and split the path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        # Traverse
        folder = self
        for segment in path[:-1]:
            folder = folder._get_resource(segment.name)

        # Set
        segment = path[-1]
        folder._set_resource(segment.name, resource)


    def _set_resource(self, name, resource):
        """
        This method is not aimed to be directly used by developers (see
        set_resource instead) nor to be redefined by sub-classes (see
        _set_file_resource and _set_folder_resource), though it could
        be if there is a good reason.
        """
        if isinstance(resource, File):
            self._set_file_resource(name, resource)
        elif isinstance(resource, Folder):
            self._set_folder_resource(name, resource)
            # Recursively add sub-resources
            source = resource
            target = self._get_resource(name)
            for name in source.get_resources():
                resource = source._get_resource(name)
                target._set_resource(name, resource)


    def del_resource(self, path):
        # Normalize and split the path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        # Traverse
        resource = self
        for segment in path[:-1]:
            resource = resource._get_resource(segment.name)

        # Delete
        segment = path[-1]
        return resource._del_resource(segment.name)


    def _del_resource(self, name):
        """
        This method is not aimed to be directly used by developers (see
        del_resource instead) nor to be redefined by sub-classes (see
        _del_file_resource and _del_folder_resource), though it could
        be if there is a good reason.
        """
        resource = self._get_resource(name)
        if isinstance(resource, File):
            self._del_file_resource(name)
        elif isinstance(resource, Folder):
            # Remove sub-resources
            for subresource_name in resource.get_resources():
                resource._del_resource(subresource_name)
            # Remove itself
            self._del_folder_resource(name)


    def del_resources(self, paths):
        for path in paths:
            self.del_resource(path)


    ######################################################################
    # Private API
    def _get_resources(self):
        """
        Returns a list with all the names of the resources.
        """
        raise NotImplementedError


    def _get_resource(self, name):
        """
        Returns the resource for the given name.
        """
        raise NotImplementedError


    def _has_resource(self, name):
        raise NotImplementedError


    def _set_file_resource(self, name, resource):
        raise NotImplementedError


    def _set_folder_resource(self, name, resource):
        raise NotImplementedError


    def _del_file_resource(self, name):
        raise NotImplementedError


    def _del_folder_resource(self, name):
        raise NotImplementedError
