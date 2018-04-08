# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006-2007, 2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
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

# Import from itools
from base import Handler
from registry import register_handler_class



class Context(object):
    """Used by 'traverse2' to control the traversal.
    """

    def __init__(self):
        self.skip = False



class Folder(Handler):
    """This is the base handler class for any folder handler. It is also used
    as the default handler class for any folder resource that has not a more
    specific handler.
    """

    class_mimetypes = ['application/x-not-regular-file']


    def __init__(self, key=None, database=None, **kw):
        if database is not None:
            self.database = database
        else:
            from database import ro_database
            self.database = ro_database
        if key is not None:
            self.key = self.database.normalize_key(key)


    def get_mtime(self):
        """Returns the last modification time.
        """
        fs = self.database.fs
        if fs.exists(self.key):
            return fs.get_mtime(self.key)
        return None


    def traverse(self):
        yield self
        for name in self.get_handler_names():
            handler = self.get_handler(name)
            if type(handler) is Folder:
                for x in handler.traverse():
                    yield x
            else:
                yield handler


    def traverse2(self, context=None):
        if context is None:
            context = Context()

        yield self, context
        if context.skip is True:
            context.skip = False
        else:
            for name in self.get_handler_names():
                handler = self.get_handler(name)
                if type(handler) is Folder:
                    for x, context in handler.traverse2(context):
                        yield x, context
                else:
                    yield handler, context
                    if context.skip is True:
                        context.skip = False


# Register
register_handler_class(Folder)
