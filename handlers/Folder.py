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


    def _load(self):
        pass


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self):
        return []


    #########################################################################
    # API
    #########################################################################
    def get_mimetype(self):
        return self.resource.get_mimetype()


    def get_resources(self, path='.'):
        return self.resource.get_resources(path)


    def get_resource(self, path):
        return self.resource.get_resource(path)


    def has_resource(self, path):
        return self.resource.has_resource(path)


    def set_resource(self, path, resource):
        return self.resource.set_resource(path, resource)


    def del_resource(self, path):
        return self.resource.del_resource(path)


    def get_handler(self, path):
        # Be sure path is a Path
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        if len(path) == 0:
            return self

        segment, path = path[0], path[1:]

        handler = None
        # Lookup the cache
        key = str(segment)
        if key in self.cache:
            handler, atime = self.cache.pop(key)
            if handler.is_outdated():
                handler = None
        # Cache miss, search the handler
        if handler is None:
            handler = self._get_handler(segment)
            # Not found
            if handler is None:
                raise ValueError, '%s not found' % segment
            # Set parent and name
            handler.parent = self
            handler.name = segment.name
        # Update the cache
        atime = datetime.datetime.now()
        self.cache[key] = (handler, atime)

        # Continue with the rest of the path
        if path:
            return handler.get_handler(path)

        return handler


    def _get_handler(self, segment):
        if self.has_resource(segment.name):
            resource = self.get_resource(segment.name)

            # Get the mimetype
            from itools.handlers import database
            mimetype = database.guess_mimetype(segment.name, resource)
            # Build and return the handler
            return database.get_handler(resource, mimetype)

        return None


    def set_handler(self, path, handler, **kw):
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        path, segment = path[:-1], path[-1]

        container = self.get_handler(path)
        container._set_handler(segment, handler, **kw)


    def _set_handler(self, segment, handler):
        self.resource.set_resource(segment.name, handler.resource)


    def del_handler(self, path):
        if not isinstance(path, uri.Path):
            path = uri.Path(path)

        container = self.get_handler(path[:-1])
        container._del_handler(path[-1])


    def _del_handler(self, segment):
        self.resource.del_resource(segment)


    ########################################################################
    # Tree
    def acquire(self, name):
        if self.has_resource(name):
            return self.get_handler(name)
        return Handler.acquire(self, name)
