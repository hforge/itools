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

# Import from the Standard Library
import mimetypes

# Import from itools
from itools import uri
from itools import i18n
from itools.types import FileName



class Resource(object):
    """
    There are two types of resources, files and folders. The generic API for
    them is:

    - get_atime(): returns the last time the object was accessed

    - get_ctime(): returns the time the object was created

    - get_mimetype(): returns the mime type of the resource (None means it
        is unknown)

    - set_mtime(mtime): sets the modification time
    """

    uri = None

    def __init__(self, uri_reference):
        if isinstance(uri_reference, uri.Reference):
            pass
        elif isinstance(uri_reference, uri.Path):
            uri_reference = uri.get_reference(str(uri_reference))
        elif isinstance(uri_reference, (str, unicode)):
            uri_reference = uri.get_reference(uri_reference)
        else:
            raise TypeError, \
                  'unexpected value of type "%s"' % type(uri_reference)

        self.uri = uri_reference


    def get_name(self):
        if self.uri:
            if self.uri.path:
                return self.uri.path[-1].name
        return None

    name = property(get_name, None, None, '')


    def get_mtime(self):
        raise NotImplementedError


    def lock(self):
        raise NotImplementedError


    def unlock(self):
        raise NotImplementedError


    def is_locked(self):
        raise NotImplementedError



class File(Resource):

    class_resource_type = 'file'


    def get_mimetype(self):
        """
        Try to guess the mimetype for a resource, given the resource itself
        and its name. To guess from the name we need to extract the type
        extension, we use an heuristic for this task, but it needs to be
        improved because there are many patterns:

        <name>                                 README
        <name>.<type>                          index.html
        <name>.<type>.<language>               index.html.en
        <name>.<type>.<language>.<encoding>    index.html.en.UTF-8
        <name>.<type>.<compression>            itools.tar.gz
        etc...

        And even more complex, the name could contain dots, or the filename
        could start by a dot (a hidden file in Unix systems).

        XXX Use magic numbers too (like file -i).
        """
        name = self.get_name()
        if name is None:
            return None

        # Parse the filename
        name, type, language = FileName.decode(name)

        # Get the mimetype
        if type is not None:
            mimetype, encoding = mimetypes.guess_type('.%s' % type)
            if mimetype is not None:
                return mimetype

        return 'application/octet-stream'


    def __getitem__(self, index):
        return self.read()[index]


    def __setitem__(self, index, value):
        raise NotImplementedError


    def __getslice__(self, a, b):
        return self.read()[a:b]


    def read(self):
        raise NotImplementedError


    def set_data(self, data):
        raise NotImplementedError


    def get_size(self):
        return len(self.read())



class Folder(Resource):

    class_resource_type = 'folder'


    def get_mimetype(self):
        return 'application/x-not-regular-file'


    ######################################################################
    # Specific folder API
    def get_resource_names(self, path='.'):
        resource = self.get_resource(path)
        return resource._get_resource_names()


    def get_resources(self, path='.'):
        resource = self.get_resource(path)
        for name in resource._get_resource_names():
            yield resource.get_resource(name)


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
            for name in source.get_resource_names():
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
            for subresource_name in resource.get_resource_names():
                resource._del_resource(subresource_name)
            # Remove itself
            self._del_folder_resource(name)


    def del_resources(self, paths):
        for path in paths:
            self.del_resource(path)


    def traverse(self):
        yield self
        for resource in self.get_resources():
            if isinstance(resource, Folder):
                for x in resource.traverse():
                    yield x
            else:
                yield resource


    ######################################################################
    # Private API
    def _get_resource_names(self):
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
