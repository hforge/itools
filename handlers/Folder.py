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
import datetime

# Import from itools
from itools.resources import base, memory
from itools import uri
from Handler import Handler



class Folder(Handler):
    """
    This is the base handler class for any folder handler. It is also used
    as the default handler class for any folder resource that has not a more
    specific handler.
    """

    class_resource_type = 'folder'


    def __init__(self, resource=None, **kw):
        self.cache = {}

        if resource is None:
            resource = memory.Folder()
            skeleton = self.get_skeleton(**kw)
        else:
            skeleton = None

        self.resource = resource

        # Add the skeleton
        if skeleton is not None:
            for name, handler in skeleton:
                self.set_handler(name, handler)

        # Load
        self.load()


    #########################################################################
    # Load / Save
    #########################################################################
    def _load(self, resource):
        """
        By default folders don't load any state. This means they are always
        up-to-date.

        Warning: if you develop a folder handler that does load its state,
        be very careful to update the state whenever you modify the handler.
        """

    def _save(self):
        pass


    #########################################################################
    # The factory
    #########################################################################
    def register_handler_class(cls, handler_class):
        raise NotImplementedError
    register_handler_class = classmethod(register_handler_class)


    def build_handler(cls, resource):
        return cls(resource)
    build_handler = classmethod(build_handler)


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self):
        return []


    #########################################################################
    # Obsolete API
    # XXX To be removed by 0.5, direct access to the resource must be done
    # through "self.resource". A new API must be developed (has_handler,
    # get_handlers, etc.)
    #########################################################################
    def get_mimetype(self):
        return self.resource.get_mimetype()


    #########################################################################
    # API (private)
    #########################################################################
    def _get_handler_names(self):
        return self.resource._get_resource_names()


    def _get_handler(self, segment, resource):
        # Build and return the handler
        return Handler.build_handler(resource)


    def _get_virtual_handler(self, segment):
        """
        This method must return a handler for the given segment, or raise
        the exception LookupError. We know there is not a resource with
        the given name, this method is used to return 'virtual' handlers.
        """
        raise LookupError, 'the resource "%s" does not exist' % segment.name


    def _set_handler(self, segment, handler):
        self.resource.set_resource(segment.name, handler.resource)


    def _del_handler(self, segment):
        self.resource.del_resource(segment)


    #########################################################################
    # API (public)
    #########################################################################
    def get_handler_names(self, path='.'):
        handler = self.get_handler('.')
        return handler._get_handler_names()


    def has_handler(self, path):
        # Normalize the path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        container = self.get_handler(path[:-1])
        return path[-1].name in container.get_handler_names()


    def get_handler(self, path):
        # Be sure path is a Path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        if len(path) == 0:
            return self

        if path[0].name == '..':
            if self.parent is None:
                raise ValueError, 'this handler is the root handler'
            return self.parent.get_handler(path[1:])

        segment, path = path[0], path[1:]
        name = segment.name

        handler = None
        # Lookup the cache
        key = str(segment)
        if key in self.cache:
            handler, atime = self.cache.pop(key)
            if handler.is_outdated():
                handler = None
        # Cache miss, search the handler
        is_virtual = False
        if handler is None:
            # Lookup the resource handler
            if self.resource.has_resource(name):
                resource = self.resource.get_resource(name)
                handler = self._get_handler(segment, resource)
            else:
                handler = self._get_virtual_handler(segment)
                is_virtual = True
            # Set parent and name
            handler.parent = self
            handler.name = segment.name
        # Update the cache
        if is_virtual is False:
            atime = datetime.datetime.now()
            self.cache[key] = (handler, atime)

        # Continue with the rest of the path
        if path:
            return handler.get_handler(path)

        return handler


    def get_handlers(self, path='.'):
        handler = self.get_handler(path)
        for name in handler.get_handler_names(path):
            yield handler.get_handler(name)


    def set_handler(self, path, handler, **kw):
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        path, segment = path[:-1], path[-1]

        container = self.get_handler(path)
        container._set_handler(segment, handler, **kw)
        # Set timestamp
        container.timestamp = datetime.datetime.now()


    def del_handler(self, path):
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        container = self.get_handler(path[:-1])
        container._del_handler(path[-1])
        # Set timestamp
        container.timestamp = datetime.datetime.now()


    ########################################################################
    # Tree
    def traverse(self):
        yield self
        for resource_name in self.get_handler_names():
            handler = self.get_handler(resource_name)
            if isinstance(handler, Folder):
                for x in handler.traverse():
                    yield x
            else:
                yield handler


    def acquire(self, name):
        if self.has_handler(name):
            return self.get_handler(name)
        return Handler.acquire(self, name)


Handler.register_handler_class(Folder)
