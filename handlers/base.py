# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools.uri import uri, Path
from itools.vfs import vfs
from exceptions import AcquisitionError
from transactions import get_transaction

"""
This module provides the abstract class which is the root in the
handler class hierarchy.
"""



class Node(object):

    parent = None

    def get_abspath(self):
        # TODO Should return a Path instance
        if self.parent is None:
            return '/'

        parent_path = self.parent.get_abspath()
        if not parent_path.endswith('/'):
            parent_path += '/'

        return parent_path + self.name

    abspath = property(get_abspath, None, None, '')


    def get_real_handler(self):
        return self.real_handler or self


    def get_physical_path(self):
        # TODO Should return a Path instance
        real = self.get_real_handler()
        return real.get_abspath()


    def get_root(self):
        if self.parent is None:
            return self
        return self.parent.get_root()


    def get_pathtoroot(self):
        i = 0
        parent = self.parent
        while parent is not None:
            parent = parent.parent
            i += 1
        if i == 0:
            return './'
        return '../' * i

##        if self.parent is None:
##            return './'
##        return self.parent.get_pathtoroot() + '../'


    def get_pathto(self, handler):
        path = Path(self.get_abspath())
        return path.get_pathto(handler.get_abspath())


    def acquire(self, name):
        if self.has_handler(name):
            return self.get_handler(name)
        if self.parent is None:
            raise AcquisitionError, name
        return self.parent.acquire(name)


    def _get_handler_names(self):
        return []


    def get_handler_names(self, path='.'):
        container = self.get_handler(path)
        return container._get_handler_names()


    def has_handler(self, path):
        # Normalize the path
        if not isinstance(path, Path):
            path = Path(path)

        path, name = path[:-1], path[-1]

        container = self.get_handler(path)
        return name in container.get_handler_names()


    def get_handler(self, path):
        # Be sure path is a Path
        if not isinstance(path, Path):
            path = Path(path)

        if path.is_absolute():
            root = self.get_root()
            path = str(path)[1:]
            return root.get_handler(path)

        if len(path) == 0:
            return self

        if path[0] == '..':
            if self.parent is None:
                raise ValueError, 'this handler is the root handler'
            return self.parent.get_handler(path[1:])

        name, path = path[0], path[1:]

        handler = self._get_virtual_handler(name)
        # Set parent and name
        handler.parent = self
        handler.name = name

        if path:
            return handler.get_handler(path)

        return handler


    def _get_virtual_handler(self, name):
        raise LookupError, 'file handlers can not be traversed'



class Handler(Node):
    """
    This class represents a resource handler; where a resource can be
    a file or a directory, and is identified by a URI. It is used as a
    base class for any other handler class.
    """

    class_mimetypes = []
    class_extension = None

    # All handlers have a uri, timestamp, parent and name, plus the state.
    # The variable class "__slots__" is to be overriden.
    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler']


    def __init__(self, ref=None, **kw):
        self.parent = None
        self.name = ''
        self.real_handler = None

        if ref is None:
            # A handler from scratch
            self.uri = None
            self.new(**kw)
            self.timestamp = None
        else:
            # Calculate the URI
            self.uri = uri.get_absolute_reference(ref)
            ##self.timestamp = None


    def __getattr__(self, name):
        if name not in self.__slots__:
            message = "'%s' object has no attribute '%s'"
            raise AttributeError, message % (self.__class__.__name__, name)
        elif name == 'timestamp':
            self.timestamp = vfs.get_mtime(self.uri)
        else:
            self.load_state()

        return getattr(self, name)


    ########################################################################
    # API
    ########################################################################
    def load_state(self):
        raise NotImplementedError


    def load_state_from(self, uri):
        raise NotImplementedError


    def copy_handler(self):
        # Deep load
        if self.uri is not None:
            self._deep_load()
        # Create and initialize the instance
        cls = self.__class__
        copy = object.__new__(cls)
        copy.uri = None
        copy.timestamp = datetime.now()
        copy.real_handler = None
        # Copy the state
        for name in cls.__slots__:
            if name in ('uri', 'timestamp', 'parent', 'name', 'real_handler'):
                continue
            value = getattr(self, name)
            value = deepcopy(value)
            setattr(copy, name, value)
        # Return the copy
        return copy


    def _deep_load(self):
        self.load_state()


    def is_outdated(self):
        if self.uri is None:
            return False

        timestamp = self.timestamp
        # It cannot be out-of-date if it has not been loaded yet
        if timestamp is None:
            return False

        mtime = vfs.get_mtime(self.uri)
        # If the resource layer does not support mtime... we are...
        if mtime is None:
            return True

        return mtime > timestamp


    def has_changed(self):
        if self.uri is None:
            return False

        timestamp = self.timestamp
        # Not yet loaded, even
        if timestamp is None:
            return False

        mtime = vfs.get_mtime(self.uri)
        # If the resource layer does not support mtime... we are...
        if mtime is None:
            return False

        return self.timestamp > mtime


    def set_changed(self):
        if self.uri is not None:
            self.timestamp = datetime.now()
            get_transaction().add(self)


    def abort_changes(self):
        if self.uri is None:
            # XXX Should do something else than just return?
            return
        for name in self.__slots__:
            if name not in ('uri', 'parent', 'name', 'real_handler'):
                delattr(self, name)


    ########################################################################
    # Indexing
    def to_text(self):
        raise NotImplementedError


    def get_mimetype(self):
        return vfs.get_mimetype(self.uri)

    mimetype = property(get_mimetype, None, None, '')

