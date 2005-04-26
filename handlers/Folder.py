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
from datetime import datetime
from sets import Set

# Import from itools
from itools.resources import base, memory
from itools import uri
from itools.handlers.Handler import Handler
from itools.handlers.transactions import get_transaction



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


    def __init__(self, resource=None, **kw):
        self.cache = {}

        if resource is None:
            self.resource = memory.Folder()
            # Add the skeleton
            skeleton = self.get_skeleton(**kw)
            for name, handler in skeleton:
                self.resource.set_resource(name, handler.resource)
        else:
            self.resource = resource

        # Load
        self.load_state()


    #########################################################################
    # Load / Save
    #########################################################################
    def _load_state(self, resource):
        # XXX This code may be optimized just checking wether there is
        # already an up-to-date handler in the cache, then it should
        # not be touched.
        self.cache = {}
        for name in self.resource.get_resource_names():
            self.cache[name] = None

        self.added_handlers = {}
        self.removed_handlers = Set()


    def _save_state(self, resource):
        # Remove handlers
        for name in self.removed_handlers:
            resource.del_resource(name)
            # Update the cache
            del self.cache[name]
        self.removed_handlers = Set()

        # Add handlers
        for name, handler in self.added_handlers.items():
            if name in self._get_handler_names():
                resource.del_resource(name)
            resource.set_resource(name, handler.resource)
            handler.resource = resource.get_resource(name)
            # Update the cache
            self.cache[name] = None
        self.added_handlers = {}


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
    # through "self.resource".
    #########################################################################
    def get_mimetype(self):
        return self.resource.get_mimetype()


    #########################################################################
    # API (private)
    #########################################################################
    def _get_handler_names(self):
        return self.cache.keys()


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


    # XXX To be removed
    def _set_handler(self, name, handler):
        if handler.has_changed():
            handler.save_state()
        self.resource.set_resource(name, handler.resource)
        self.cache[name] = None
        self.timestamp = self.resource.get_mtime()


    # XXX To be removed
    def _del_handler(self, name):
        self.resource.del_resource(name)
        del self.cache[name]
        self.timestamp = self.resource.get_mtime()


    #########################################################################
    # API (public)
    #########################################################################
    def get_handler_names(self, path='.'):
        container = self.get_handler(path)
        handler_names = [ x for x in container._get_handler_names()
                          if x not in container.removed_handlers ]
        handler_names.extend(container.added_handlers.keys())
        return handler_names


    def has_handler(self, path):
        # Normalize the path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        path, segment = path[:-1], path[-1]
        name = segment.name

        container = self.get_handler(path)
        return name in container.get_handler_names()


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

        if name in self.added_handlers:
            # It is a new handler (added but not yet saved)
            handler = self.added_handlers[name]
        else:
            if name in self.cache and name not in self.removed_handlers:
                # Real handler
                handler = self.cache[name]
                if handler is None:
                    # Miss
                    resource = self.resource.get_resource(name)
                    handler = self._get_handler(segment, resource)
                    # Update the cache
                    self.cache[name] = handler
                else:
                    # Hit (XXX we should check wether resource and
                    # handler.resource are the same or not)
                    if handler.is_outdated():
                        handler.load_state()
                handler.is_virtual = False
            else:
                # Virtual handler
                if name in self.cache:
                    # Hit. Clean the cache (virtual handlers are not cached)
                    del self.cache[name]
                # Maybe we found a virtual handler
                handler = self._get_virtual_handler(segment)
                handler.is_virtual = True
        # Set parent and name
        handler.parent = self
        handler.name = name

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
        name = segment.name

        container = self.get_handler(path)
        # Check if there is already a handler with that name
        if name in container.get_handler_names():
            raise LookupError, 'there is already a handler named "%s"' % name

        # Store the container in the transaction
        container.set_changed()
        # Clean the 'removed_handlers' data structure if needed
        if name in container.removed_handlers:
            container.removed_handlers.remove(name)
        # Make a copy of the handler
        handler = handler.copy_handler()
        handler.parent = self
        handler.name = name
        handler.is_virtual = False
        # Add the handler
        container.added_handlers[name] = handler
        # Event, on set handler
        if hasattr(container, 'on_set_handler'):
            container.on_set_handler(segment, handler, **kw)
        # Set timestamp
        self.timestamp = datetime.now()


    def del_handler(self, path):
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        path, segment = path[:-1], path[-1]
        name = segment.name

        container = self.get_handler(path)
        # Check wether the handler really exists
        if name not in container.get_handler_names():
            raise LookupError, 'there is not any handler named "%s"' % name

        # Store the container in the transaction
        container.set_changed()
        # Event, on del handler
        if hasattr(container, 'on_del_handler'):
            container.on_del_handler(segment)
        # Clean the 'added_handlers' data structure if needed
        if name in container.added_handlers:
            del container.added_handlers[name]
        # Mark the handler as deleted
        container.removed_handlers.add(name)
        # Set timestamp
        self.timestamp = datetime.now()


    ########################################################################
    # Other methods
    def copy_handler(self):
        resource = memory.Folder()
        for handler in self.traverse():
            if handler is not self:
                path = self.get_pathto(handler)
                resource.set_resource(path, handler.resource)
        self.save_state(resource)
        return self.__class__(resource)


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


    def acquire(self, name):
        if self.has_handler(name):
            return self.get_handler(name)
        return Handler.acquire(self, name)


Handler.register_handler_class(Folder)
