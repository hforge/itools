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

"""This module provides the abstract class which is the root in the
handler class hierarchy.
"""

# Import from itools
from itools.uri import resolve_uri2
from itools import vfs
from messages import MSG_NOT_ATTACHED



class Handler(object):
    """This class represents a resource handler; where a resource can be a
    file or a directory, and is identified by a URI. It is used as a base
    class for any other handler class.
    """

    class_mimetypes = []
    class_extension = None

    # By default handlers are not attached to a database, nor a URI
    database = None
    uri = None


    ########################################################################
    # API / Safe VFS operations
    ########################################################################
    def safe_make_file(self, reference):
        if self.database is None:
            return vfs.make_file(reference)

        return self.database.safe_make_file(reference)


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
    def has_handler(self, reference):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = resolve_uri2(self.uri, reference)
        return self.database.has_handler(uri)


    def get_handler_names(self, reference='.'):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = resolve_uri2(self.uri, reference)
        return self.database.get_handler_names(uri)


    def get_handler(self, reference, cls=None):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = resolve_uri2(self.uri, reference)
        return self.database.get_handler(uri, cls=cls)


    def get_handlers(self, reference='.'):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = resolve_uri2(self.uri, reference)
        return self.database.get_handlers(uri)


    def set_handler(self, reference, handler):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = resolve_uri2(self.uri, reference)
        self.database.set_handler(uri, handler)


    def del_handler(self, reference):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = resolve_uri2(self.uri, reference)
        self.database.del_handler(uri)


    def copy_handler(self, source, target):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        source = resolve_uri2(self.uri, source)
        target = resolve_uri2(self.uri, target)
        self.database.copy_handler(source, target)


    def move_handler(self, source, target):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        source = resolve_uri2(self.uri, source)
        target = resolve_uri2(self.uri, target)
        self.database.move_handler(source, target)


    def get_mimetype(self):
        return vfs.get_mimetype(self.uri)

