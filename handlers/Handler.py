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
from itools.resources import base
from itools.handlers.transactions import get_transaction
from base import Node



class State(object):
    pass


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
        resource.open()
        try:
            self._save_state(resource)
        finally:
            resource.close()
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
    handler_class_registry = []

    @classmethod
    def register_handler_class(cls, handler_class):
        if 'handler_class_registry' not in cls.__dict__:
            cls.handler_class_registry = []
        cls.handler_class_registry.append(handler_class)


    @classmethod
    def get_handler_class(cls, resource):
        mimetype = resource.get_mimetype()
        if mimetype is not None:
            registry = cls.__dict__.get('handler_class_registry', [])
            for handler_class in registry:
                if handler_class.is_able_to_handle_mimetype(mimetype):
                    return handler_class.get_handler_class(resource)
        return cls


    @classmethod
    def is_able_to_handle_mimetype(cls, mimetype):
        # Check wether this class understands this mimetype
        type, subtype = mimetype.split('/')
        for class_mimetype in cls.class_mimetypes:
            class_type, class_subtype = class_mimetype.split('/')
            if type == class_type:
                if subtype == class_subtype:
                    return True
                if class_subtype == '*':
                    return True
        # Check wether any sub-class is able to handle the mimetype
        for handler_class in cls.__dict__.get('handler_class_registry', []):
            if handler_class.is_able_to_handle_mimetype(mimetype):
                return True
        # Everything failed, we are not able to manage the mimetype
        return False


    @classmethod
    def build_handler(cls, resource, **kw):
        handler_class = cls.get_handler_class(resource, **kw)
        return handler_class(resource)
