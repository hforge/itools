# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
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
        return self


    def get_physical_path(self):
        # TODO Should return a Path instance
        return self.get_abspath()


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

        raise LookupError, 'file handlers can not be traversed'



class Handler(Node):
    """
    This class represents a resource handler; where a resource can be
    a file or a directory, and is identified by a URI. It is used as a
    base class for any other handler class.
    """

    class_mimetypes = []
    class_extension = None

    # Instance variables. The variable class "__slots__" is to be overriden.
    __slots__ = ['database', 'uri', 'timestamp', 'dirty', 'parent', 'name']


    ########################################################################
    # API / Safe VFS operations
    ########################################################################
    def safe_make_file(self, reference):
        if self.database is None:
            return vfs.make_file(reference)

        return self.database.safe_make_file(reference)


    def safe_make_folder(self, reference):
        if self.database is None:
            return vfs.make_folder(reference)

        return self.database.safe_make_folder(reference)


    def safe_remove(self, reference):
        if self.database is None:
            return vfs.remove(reference)

        return self.database.safe_remove(reference)


    def safe_open(self, reference, mode=None):
        if self.database is None:
            return vfs.open(reference, mode=mode)

        return self.database.safe_open(reference, mode=mode)


    ########################################################################
    # API
    ########################################################################
    def to_text(self):
        raise NotImplementedError


    def get_mimetype(self):
        return vfs.get_mimetype(self.uri)

    mimetype = property(get_mimetype, None, None, '')

