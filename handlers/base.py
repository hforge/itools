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

MSG_NOT_ATTACHED = 'method only available when attached to a database'


class Handler(object):
    """
    This class represents a resource handler; where a resource can be
    a file or a directory, and is identified by a URI. It is used as a
    base class for any other handler class.
    """

    class_mimetypes = []
    class_extension = None

    # Instance variables. The variable class "__slots__" is to be overriden.
    # FIXME The 'parent' and 'name' variables are not used by the handlers
    # layer, but by itools.web, so they should not be defined here.
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
    def has_handler(self, path):
        # Normalize the path
        if not isinstance(path, Path):
            path = Path(path)

        path, name = path[:-1], path[-1]

        container = self.get_handler(path)
        return name in container.get_handler_names()


    def get_handler_names(self, reference='.'):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = self.uri.resolve2(reference)
        return self.database.get_handler_names(uri)


    def get_handler(self, reference, cls=None):
        database = self.database
        if database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = self.uri.resolve2(reference)
        return self.database.get_handler(uri, cls=cls)


    def to_text(self):
        raise NotImplementedError


    def get_mimetype(self):
        return vfs.get_mimetype(self.uri)

    mimetype = property(get_mimetype, None, None, '')

