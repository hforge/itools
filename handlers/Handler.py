# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
This module provides the abstract class which is the root in the
handler class hierarchy.
"""

# Import from the Standard Library
import datetime
import thread

# Import from itools
from itools.uri import Path
from itools.resources import base
from itools.handlers.transactions import get_transaction



class AcquisitionError(LookupError):
    pass



class State(object):
    pass


class Node(object):

    def get_abspath(self):
        # XXX Should return a Path instance
        if self.parent is None:
            return '/'

        parent_path = self.parent.get_abspath()
        if not parent_path.endswith('/'):
            parent_path += '/'

        return parent_path + self.name

    abspath = property(get_abspath, None, None, '')


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


    def acquire(self, name):
        if self.parent is None:
            raise AcquisitionError, name
        return self.parent.acquire(name)


    def _get_handler_names(self):
        return []


    def get_handler_names(self, path='.'):
        container = self.get_handler(path)
        return container._get_handler_names()


    def has_handler(self, path):
        # Normalize the path
        if not isinstance(path, Path):
            path = Path(path)

        path, segment = path[:-1], path[-1]
        name = segment.name

        container = self.get_handler(path)
        return name in container.get_handler_names()


    def get_handler(self, path):
        from Folder import build_virtual_handler
        # Be sure path is a Path
        if not isinstance(path, Path):
            path = Path(path)

        if path.is_absolute():
            root = self.get_root()
            path = str(path)[1:]
            return root.get_handler(path)

        if len(path) == 0:
            return self

        if path[0].name == '..':
            if self.parent is None:
                raise ValueError, 'this handler is the root handler'
            return self.parent.get_handler(path[1:])

        segment, path = path[0], path[1:]
        name = segment.name

        handler = self._get_virtual_handler(segment)
        handler = build_virtual_handler(handler)
        # Set parent and name
        handler.parent = self
        handler.name = name

        if path:
            return handler.get_handler(path)

        return handler


    def _get_virtual_handler(self, segment):
        raise LookupError, 'file handlers can not be traversed'





class Handler(Node):
    """
    This class represents a resource handler, where a resource can be
    a file, a directory or a link. It is used as a base class for any
    other handler class.
    """

    class_mimetypes = []
    class_extension = None


    # By default the handler is a free node (does not belong to a tree, or
    # is the root of a tree).
    parent = None
    name = ''
    real_handler = None


    ########################################################################
    # API
    ########################################################################
    def get_mimetype(self):
        return self.resource.get_mimetype()

    mimetype = property(get_mimetype, None, None, '')


    ########################################################################
    # Load / Save
    def load_state(self, resource=None):
        if resource is None:
            resource = self.resource
            update = False
        else:
            update = True

        resource.open()
        self._load_state(resource)
        resource.close()
        self.timestamp = resource.get_mtime()
        if update:
            self.set_changed()


    def save_state(self, resource=None):
        if resource is None:
            resource = self.resource

        transaction = get_transaction()
        transaction.lock()
        resource_transaction = resource.get_transaction()
        try:
            resource.open()
            self._save_state(resource)
        except:
            resource.close()
            if resource_transaction is not None:
                resource_transaction.abort()
            transaction.release()
            raise
        else:
            resource.close()
            if resource_transaction is not None:
                resource_transaction.commit()
            if resource is self.resource:
                if self in transaction:
                    transaction.remove(self)
                self.timestamp = resource.get_mtime()
            transaction.release()


    def is_outdated(self):
        mtime = self.resource.get_mtime()
        if mtime is None:
            return True
        return mtime > self.timestamp


    def has_changed(self):
        mtime = self.resource.get_mtime()
        if mtime is None:
            return False
        return self.timestamp > mtime


    def set_changed(self):
        get_transaction().add(self)


    ########################################################################
    # The factory
    handler_class_registry = {}

    @classmethod
    def register_handler_class(cls, handler_class):
        resource_type = handler_class.class_resource_type
##        if resource_type in cls.handler_class_registry:
##            log
        cls.handler_class_registry[resource_type] = handler_class


    @classmethod
    def build_handler(cls, resource):
        resource_type = resource.class_resource_type
        if resource_type in cls.handler_class_registry:
            handler_class = cls.handler_class_registry[resource_type]
            return handler_class.build_handler(resource)
        raise ValueError, 'unknown resource type "%s"' % resource_type
