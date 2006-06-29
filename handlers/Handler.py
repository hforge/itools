# -*- coding: ISO-8859-1 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
This module provides the abstract class which is the root in the
handler class hierarchy.
"""

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools import vfs
from itools.handlers.transactions import get_transaction
from base import Node



class Handler(Node):
    """
    This class represents a resource handler; where a resource can be
    a file or a directory, and is identified by a URI. It is used as a
    base class for any other handler class.
    """

    class_mimetypes = []
    class_extension = None

    # All handlers have a uri and a timestamp, plus the state.
    # The variable class "__slots__" is to be overriden.
    __slots__ = ['uri', 'timestamp']


    def __init__(self, uri=None, **kw):
        self.timestamp = None
        if uri is None:
            # A handler from scratch
            self.uri = None
            self.new(**kw)
        else:
            # Calculate the URI
            self.uri = vfs.get_absolute_reference(uri)


    def __getattr__(self, name):
        if name not in self.__slots__:
            message = "'%s' object has no attribute '%s'"
            raise AttributeError, message % (self.__class.__name__, name)

        self.load_state()
        return getattr(self, name)


    # By default the handler is a free node (does not belong to a tree, or
    # is the root of a tree).
    parent = None
    name = ''
    real_handler = None


    ########################################################################
    # API
    ########################################################################
    def copy_handler(self):
        # Deep load
        self._deep_load()
        # Create and initialize the instance
        cls = self.__class__
        copy = object.__new__(cls)
        copy.uri = None
        copy.timestamp = None
        # Copy the state
        for name in cls.__slots__:
            if name == 'uri' or name == 'timestamp':
                continue
            value = getattr(self, name)
            value = deepcopy(value)
            setattr(copy, name, value)
        # Return the copy
        return copy


    def _deep_load(self):
        self.load_state()


    def load_state(self):
        resource = vfs.open(self.uri)
        with resource:
            self._load_state(resource)
        self.timestamp = vfs.get_mtime(self.uri)


    def load_state_from(self, uri):
        resource = vfs.open(uri)
        get_transaction().add(self)
        with resource:
            self._load_state(resource)
        self.timestamp = datetime.now()


    def save_state(self):
        transaction = get_transaction()
        transaction.lock()
        resource = vfs.open(self.uri)
        try:
            self._save_state(resource)
        finally:
            resource.close()
            transaction.release()


    def save_state_to(self, resource):
        transaction = get_transaction()
        transaction.lock()
        resource.open()
        try:
            self._save_state_to(resource)
        finally:
            resource.close()
            transaction.release()


    def _save_state(self, resource):
        self._save_state_to(resource)


    def is_outdated(self):
        timestamp = self.timestamp
        # It cannot be out-of-date if it has not been loaded yet
        if timestamp is None:
            return False

        mtime = self.resource.get_mtime()
        # If the resource layer does not support mtime... we are...
        if mtime is None:
            return True

        return mtime > timestamp


    def has_changed(self):
        timestamp = self.timestamp
        # Not yet loaded, even
        if timestamp is None:
            return False

        mtime = self.resource.get_mtime()
        # If the resource layer does not support mtime... we are...
        if mtime is None:
            return False

        return self.timestamp > mtime


    def set_changed(self):
        if self.resource is not None:
            self.timestamp = datetime.now()
            get_transaction().add(self)


    ########################################################################
    # XXX Obsolete.
    # To be removed by 0.5, use instead "self.resource.get_mimetype".
    def get_mimetype(self):
        return self.resource.get_mimetype()

    mimetype = property(get_mimetype, None, None, '')

