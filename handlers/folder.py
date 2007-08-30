# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.uri import Path, get_absolute_reference
from itools.vfs import vfs
from base import Handler
import registry



MSG_NOT_ATTACHED = 'method only available when attached to a database'


class Context(object):
    """Used by 'traverse2' to control the traversal."""

    def __init__(self):
        self.skip = False



class Folder(Handler):
    """
    This is the base handler class for any folder handler. It is also used
    as the default handler class for any folder resource that has not a more
    specific handler.
    """

    class_resource_type = 'folder'
    class_mimetypes = ['application/x-not-regular-file']


    __slots__ = ['database', 'uri', 'timestamp', 'dirty', 'parent', 'name',
                 'cache']


    def __init__(self, ref=None, **kw):
        self.database = None
        self.timestamp = None
        self.dirty = False
        self.parent = None
        self.name = ''

        if ref is None:
            # A handler from scratch
            self.uri = None
            self.cache = {}
            self.new(**kw)
        else:
            # Calculate the URI
            self.uri = get_absolute_reference(ref)
            self.cache = None


    def new(self, **kw):
        pass


    #########################################################################
    # API (public)
    #########################################################################
    def has_handler(self, reference):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = self.uri.resolve2(reference)
        return self.database.has_handler(uri)


    def get_handlers(self, reference='.'):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = self.uri.resolve2(reference)
        return self.database.get_handlers(uri)


    def set_handler(self, reference, handler):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = self.uri.resolve2(reference)
        self.database.set_handler(uri, handler)


    def del_handler(self, reference):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        uri = self.uri.resolve2(reference)
        self.database.del_handler(uri)


    def move_handler(self, source, target):
        if self.database is None:
            raise NotImplementedError, MSG_NOT_ATTACHED

        source = self.uri.resolve2(source)
        target = self.uri.resolve2(target)
        self.database.move_handler(source, target)


    ########################################################################
    # Tree
    def traverse(self):
        yield self
        for name in self.get_handler_names():
            handler = self.get_handler(name)
            if isinstance(handler, Folder):
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
                if isinstance(handler, Folder):
                    for x, context in handler.traverse2(context):
                        yield x, context
                else:
                    yield handler, context
                    if context.skip is True:
                        context.skip = False


registry.register_handler_class(Folder)
