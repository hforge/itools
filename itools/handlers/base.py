# Copyright (C) 2003-2007, 2009-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006-2007, 2010 Hervé Cauwelier <herve@oursours.net>
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


MSG_NOT_ATTACHED = 'Method only available when attached to a database.'


class Handler:
    """This class represents a resource handler; where a resource can be a
    file or a directory, and is identified by a unique key.

    It is used as a base class for any other handler class.
    """

    class_mimetypes = []
    class_extension = None

    # By default handlers are not attached to a database, nor a URI
    database = None
    key = None

    def has_handler(self, reference):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        key = database.resolve2(self.key, reference)
        return database.has_handler(key)

    def get_handler_names(self, reference='.'):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        key = database.resolve2(self.key, reference)
        return database.get_handler_names(key)

    def get_handler(self, reference, cls=None, soft=False):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        key = database.resolve2(self.key, reference)
        return database._get_handler(key, cls, soft)

    def get_handlers(self, reference='.'):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        key = database.resolve2(self.key, reference)
        return database.get_handlers(key)

    def set_handler(self, reference, handler):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        key = database.resolve2(self.key, reference)
        database.set_handler(key, handler)

    def del_handler(self, reference):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        key = database.resolve2(self.key, reference)
        database.del_handler(key)

    def copy_handler(self, source, target, exclude_patterns=None):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        source = database.resolve2(self.key, source)
        target = database.resolve2(self.key, target)
        database.copy_handler(source, target, exclude_patterns)

    def move_handler(self, source, target):
        database = self.database
        if database is None:
            raise NotImplementedError(MSG_NOT_ATTACHED)

        source = database.resolve2(self.key, source)
        target = database.resolve2(self.key, target)
        database.move_handler(source, target)

    def get_mimetype(self):
        return self.database.get_mimetype(self.key)
