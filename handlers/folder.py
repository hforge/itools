# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.uri import Path, get_absolute_reference
from itools.vfs import vfs
from base import Handler
import registry



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

    
    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'cache', 'added_handlers', 'removed_handlers']


    def new(self, **kw):
        self.cache = {}
        self.added_handlers = set()
        self.removed_handlers = set()


    def _load_state(self):
        # XXX This code may be optimized just checking wether there is
        # already an up-to-date handler in the cache, then it should
        # not be touched.
        cache = {}
        for name in vfs.get_names(self.uri):
            cache[name] = None
        self.cache = cache

        # Keep differential
        self.added_handlers = set()
        self.removed_handlers = set()


    def load_state(self):
        self._load_state()
        self.timestamp = vfs.get_mtime(self.uri)


    def _deep_load(self):
        self.load_state()
        for name in self.cache:
            handler = self.get_handler(name)
            handler._deep_load()


    def save_state(self):
        cache = self.cache
        # Remove
        folder = vfs.open(self.uri)
        for name in self.removed_handlers:
            folder.remove(name)
        self.removed_handlers = set()

        # Add
        base = self.uri
        for name in self.added_handlers:
            # Remove the handler if it exists
            if folder.exists(name):
                folder.remove(name)
            # Add the handler
            target = base.resolve2(name)
            handler = cache[name]
            handler.save_state_to(target)
            # Clean the cache (the most simple and robust option)
            cache[name] = None
        self.added_handlers = set()
        # Update the timestamp
        self.timestamp = vfs.get_mtime(self.uri)


    def save_state_to(self, uri):
        # Create the target folder
        vfs.make_folder(uri)
        # Add all the handlers
        base = get_absolute_reference(uri)
        for name in self.cache:
            handler = self.get_handler(name)
            target = base.resolve2(name)
            handler.save_state_to(target)


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
        copy.cache = {}
        copy.added_handlers = set()
        copy.removed_handlers = set()
        for name in self.cache:
            copy.cache[name] = self.cache[name].copy_handler()
        # Return the copy
        return copy


    #########################################################################
    # API (private)
    #########################################################################
    def _get_handler_names(self):
        return self.cache.keys()


    def get_handler_class(self, uri):
        return registry.get_handler_class(uri)


    def _get_virtual_handler(self, name):
        """
        This method must return a handler for the given name, or raise
        the exception LookupError. We know there is not a resource with
        the given name, this method is used to return 'virtual' handlers.
        """
        raise LookupError, 'the resource "%s" does not exist' % name


    def _get_handler(self, name, uri):
        handler_class = self.get_handler_class(uri)
        return handler_class(uri)


    #########################################################################
    # API (public)
    #########################################################################
    def get_handler(self, path, caching=True):
        # Be sure path is a Path
        if not isinstance(path, Path):
            path = Path(path)

        if path.is_absolute():
            root = self.get_root()
            path = str(path)[1:]
            return root.get_handler(path, caching=caching)

        if len(path) == 0:
            return self

        if path[0] == '..':
            if self.parent is None:
                raise ValueError, 'this handler is the root handler'
            return self.parent.get_handler(path[1:], caching=caching)

        here = self
        for name in path:
            # Check wether it is a folder or not
            if not isinstance(here, Folder):
                # Virtual handler
                handler = here._get_virtual_handler(name)
                # Set parent and name
                handler.parent = here
                handler.name = name

                here = handler
                continue

            # Check wether the resource exists or not
            if name not in here.cache:
                # Virtual handler
                handler = here._get_virtual_handler(name)
                handler = build_virtual_handler(handler)
                # Attach
                handler.parent = here
                handler.name = name

                here = handler
                continue

            # Check if it is a new handler (avoid cache)
            if name in here.added_handlers:
                here = here.cache[name]
                continue

            # Get the handler from the cache
            handler = here.cache[name]
            if handler is None:
                # Miss
                uri = here.uri.resolve2(name)
                handler = here._get_handler(name, uri)
                # Update the cache
                if caching is True:
                    here.cache[name] = handler
            else:
                # Hit, reload the handler if needed
                if handler.is_outdated():
                    handler.load_state()

            # Attach
            handler.parent = here.get_real_handler()
            handler.name = name

            # Virtual handlers propagate
            if here.real_handler is not None:
                handler = build_virtual_handler(handler)
                # Attach
                handler.parent = here
                handler.name = name

            # Next
            here = handler

        return here


    def has_handler(self, path):
        try:
            self.get_handler(path)
        except LookupError:
            return False

        return True


    def get_handler_names(self, path='.'):
        container = self.get_handler(path)
        return container._get_handler_names()


    def _get_handler_names(self):
        return self.cache.keys()


    def get_handlers(self, path='.'):
        handler = self.get_handler(path)
        for name in handler.get_handler_names(path):
            yield handler.get_handler(name)


    def _set_handler(self, name, handler):
        handler.parent = self
        handler.name = name
        self.cache[name] = handler


    def set_handler(self, path, handler):
        if not isinstance(path, Path):
            path = Path(path)

        path, name = path[:-1], path[-1]

        container = self.get_handler(path)
        container = container.get_real_handler()
        # Check if there is already a handler with that name
        if name in container.get_handler_names():
            raise LookupError, 'there is already a handler named "%s"' % name

        # Make a copy of the handler
        handler = handler.copy_handler()
        # Store the container in the transaction
        container.set_changed()
        # Clean the 'removed_handlers' data structure if needed
        if name in container.removed_handlers:
            container.removed_handlers.remove(name)

        # Add the handler
        container.added_handlers.add(name)
        container._set_handler(name, handler)

        return handler


    def del_handler(self, path):
        if not isinstance(path, Path):
            path = Path(path)

        path, name = path[:-1], path[-1]

        container = self.get_handler(path)
        # Check wether the handler really exists
        if name not in container.get_handler_names():
            raise LookupError, 'there is not any handler named "%s"' % name

        # Store the container in the transaction
        container.set_changed()
        # Clean the 'added_handlers' data structure if needed
        if name in container.added_handlers:
            container.added_handlers.remove(name)
        # Mark the handler as deleted
        container.removed_handlers.add(name)
        del container.cache[name]


    ########################################################################
    # Other methods
    def after_set_handler(self, name, handler, **kw):
        pass


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


    def traverse2(self, context=None, caching=True):
        if context is None:
            context = Context()

        yield self, context
        if context.skip is True:
            context.skip = False
        else:
            for name in self.get_handler_names():
                handler = self.get_handler(name, caching=caching)
                if isinstance(handler, Folder):
                    for x, context in handler.traverse2(context, caching=caching):
                        yield x, context
                else:
                    yield handler, context
                    if context.skip is True:
                        context.skip = False



def build_virtual_handler(handler):
    """
    Makes a clone of the given handler.
    """
    handler = handler.get_real_handler()
    virtual_handler = Handler.__new__(handler.__class__)

    for name in handler.__slots__:
        if name in ('parent', 'name', 'real_handler'):
            continue
        value = getattr(handler, name)
        setattr(virtual_handler, name, value)

    # Keep a reference to the real handler
    virtual_handler.real_handler = handler

    return virtual_handler
    

registry.register_handler_class(Folder)
