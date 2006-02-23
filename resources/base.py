# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import mimetypes

# Import from itools
from itools import uri
from itools.datatypes import FileName



class Context(object):
    """Used by 'traverse2' to control the traversal."""

    def __init__(self):
        self.skip = False



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
            message = 'unexpected value of type "%s"' % type(uri_reference)
            raise TypeError, message

        self.uri = uri_reference


    def get_name(self):
        if self.uri:
            if self.uri.path:
                return self.uri.path[-1].name
        return None

    name = property(get_name, None, None, '')


    def get_mtime(self):
        raise NotImplementedError


    ##########################################################################
    # Open/Close
    ##########################################################################
    def open(self):
        raise NotImplementedError


    def close(self):
        raise NotImplementedError


    def is_open(self):
        raise NotImplementedError


    ##########################################################################
    # Locking (prevent other threads to touch the resource)
    ##########################################################################
    def lock(self):
        raise NotImplementedError


    def unlock(self):
        raise NotImplementedError


    def is_locked(self):
        raise NotImplementedError


    ##########################################################################
    # Transactions
    ##########################################################################
    def get_transaction(self):
        pass



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


    ######################################################################
    # API / Information
    ######################################################################
    def get_size(self):
        raise NotImplementedError


    ######################################################################
    # API / Sequential access
    ######################################################################
    def read(self, size=None):
        raise NotImplementedError


    def readline(self):
        raise NotImplementedError


    def readlines(self):
        while True:
            line = self.readline()
            if line:
                yield line
            else:
                break


    def write(self, data):
        raise NotImplementedError


    def truncate(self, size=None):
        raise NotImplementedError


    ######################################################################
    # API / Direct access
    ######################################################################
    def seek(self, offset, whence=0):
        raise NotImplementedError


    def tell(self):
        raise NotImplementedError


    # XXX To be removed, because it makes the behaviour of file resources
    # different from the behaviour of Python files (#151). In particular
    # "for x in resource" iterates over each character in the resource,
    # while it should iterate over each line. This breaks the "csv" Python
    # module, for instance.
    def __getitem__(self, index):
        self.seek(index)
        return self.read(1)


    def __setitem__(self, index, value):
        self.seek(index)
        self.write(value)


    def __getslice__(self, a, b):
        self.seek(a)
        return self.read(b-a)


    def __setslice__(self, start, stop, value):
        self.seek(start)
        self.write(value)


    def append(self, data):
        self.seek(0, 2)
        self.write(data)



class Folder(Resource):

    class_resource_type = 'folder'


    def get_mimetype(self):
        return 'application/x-not-regular-file'


    def open(self):
        pass


    def close(self):
        pass


    def is_open(self):
        return True


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
            resource.open()
            self._set_file_resource(name, resource)
            resource.close()
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


    def traverse2(self, context=None):
        if context is None:
            context = Context()

        yield self, context
        if context.skip is True:
            context.skip = False
        else:
            for resource in self.get_resources():
                if isinstance(resource, Folder):
                    for x, context in resource.traverse2(context):
                        yield x, context
                else:
                    yield resource, context
                    if context.skip is True:
                        context.skip = False


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
