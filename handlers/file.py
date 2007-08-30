# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from copy import deepcopy
from cStringIO import StringIO
import datetime

# Import from itools
from itools.uri import uri
from itools.vfs import vfs
from registry import register_handler_class
from base import Handler



class File(Handler):
    """
    This is the base handler class for any file handler. It is also used
    as the default handler class for any file resource that has not a more
    specific handler.
    """

    class_resource_type = 'file'


    __slots__ = ['database', 'uri', 'timestamp', 'dirty', 'parent', 'name',
                 'data']


    def __init__(self, ref=None, string=None, **kw):
        self.database = None
        self.timestamp = None
        self.dirty = False
        self.parent = None
        self.name = ''

        if ref is None:
            self.uri = None
            if string is not None:
                # A handler from a byte string
                self.load_state_from_string(string)
            else:
                # A handler from some input data
                self.new(**kw)
        else:
            # Calculate the URI
            self.uri = uri.get_absolute_reference(ref)


    def new(self, data=''):
        self.data = data


    def __getattr__(self, name):
        if name not in self.__slots__:
            message = "'%s' object has no attribute '%s'"
            raise AttributeError, message % (self.__class__.__name__, name)

        # Lazy load
        self.load_state()
        return getattr(self, name)


    #########################################################################
    # Load / Save
    #########################################################################
    def _load_state_from_file(self, file):
        """Method to be overriden by sub-classes."""
        self.data = file.read()


    def load_state(self):
        # XXX Use "with" once "urllib.urlopen" supports it
        file = vfs.open(self.uri, 'r')
        try:
            self._load_state_from_file(file)
        finally:
            file.close()
        self.timestamp = vfs.get_mtime(self.uri)
        self.dirty = False


    def load_state_from(self, uri):
        with vfs.open(uri) as file:
            self.load_state_from_file(file)


    def load_state_from_file(self, file):
        self.set_changed()
        self._load_state_from_file(file)


    def load_state_from_string(self, string):
        file = StringIO(string)
        self.load_state_from_file(file)


    def save_state(self):
        with self.safe_open(self.uri, 'w') as file:
            self.save_state_to_file(file)
        # Update the timestamp
        self.timestamp = vfs.get_mtime(self.uri)
        self.dirty = False


    def save_state_to(self, uri):
        with self.safe_make_file(uri) as file:
            self.save_state_to_file(file)


    def save_state_to_file(self, file):
        # We call "to_str" so this method will be good for sub-classes
        data = self.to_str()
        # Write and truncate (calls to "_save_state" must be done with the
        # pointer pointing to the beginning)
        file.write(data)
        file.truncate()


    def clone(self, cls=None):
        # Create and initialize the instance
        if cls is None:
            cls = self.__class__
        copy = object.__new__(cls)
        copy.database = None
        copy.uri = None
        copy.timestamp = None
        copy.dirty = False
        # Copy the state
        exclude = set(['database', 'uri', 'timestamp', 'dirty', 'parent',
                       'name'])
        for name in cls.__slots__:
            if name not in exclude:
                value = getattr(self, name)
                value = deepcopy(value)
                setattr(copy, name, value)
        # Return the copy
        return copy


    def is_outdated(self):
        if self.uri is None:
            return False

        timestamp = self.timestamp
        # It cannot be out-of-date if it has not been loaded yet
        if timestamp is None:
            return False

        mtime = vfs.get_mtime(self.uri)
        # If the resource layer does not support mtime... we are...
        if mtime is None:
            return True

        return mtime > timestamp


    def set_changed(self):
        if self.uri is not None:
            self.dirty = True
            database = self.database
            if database is not None:
                if self.uri not in database.added:
                    database.changed.add(self.uri)


    def abort_changes(self):
        # Not attached to a URI
        if self.uri is None:
            return
        # Not changed
        if self.dirty is False:
            return
        # Abort
        exclude = set(['database', 'uri', 'timestamp', 'dirty', 'parent',
                       'name'])
        for name in self.__slots__:
            if name not in exclude:
                delattr(self, name)
        self.timestamp = None
        self.dirty = False


    #########################################################################
    # API
    #########################################################################
    def to_str(self):
        return self.data


    def set_data(self, data):
        self.set_changed()
        self.data = data


register_handler_class(File)
