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
from datetime import datetime

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

    # By default the handler is not loaded (we encourage lazy load), so
    # the timestamp is set to None
    timestamp = None


    def __init__(self, resource=None, **kw):
        self.resource = resource
        if resource is None:
            self.new(**kw)
        else:
            self.load_state()


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
    def load_state(self):
        resource = self.resource
        resource.open()
        try:
            self._load_state(resource)
        finally:
            resource.close()
        self.timestamp = resource.get_mtime()


    def load_state_from(self, resource):
        resource.open()
        get_transaction().add(self)
        try:
            self._load_state(resource)
        finally:
            resource.close()
        self.timestamp = datetime.now()


    def save_state(self):
        resource = self.resource

        transaction = get_transaction()
        transaction.lock()
        resource.open()
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
            self._save_state(resource)
        finally:
            resource.close()
            transaction.release()


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

