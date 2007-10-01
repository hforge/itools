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


    __slots__ = ['uri', 'timestamp', 'parent', 'real_handler', 'name', 'data']


    def __init__(self, ref=None, string=None, **kw):
        self.parent = None
        self.name = ''
        self.real_handler = None

        if ref is None:
            self.uri = None
            if string is not None:
                # A handler from a byte string
                self.load_state_from_string(string)
            else:
                # A handler from some input data
                self.new(**kw)
            self.timestamp = None
        else:
            # Calculate the URI
            self.uri = uri.get_absolute_reference(ref)
            ##self.timestamp = None


    def new(self, data=''):
        self.data = data


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


    def load_state_from(self, uri):
        file = vfs.open(uri)
        try:
            self.load_state_from_file(file)
        finally:
            file.close()


    def load_state_from_file(self, file):
        self.set_changed()
        self._load_state_from_file(file)


    def load_state_from_string(self, string):
        file = StringIO(string)
        self.load_state_from_file(file)


    def save_state(self):
        file = vfs.open(self.uri, 'w')
        try:
            self.save_state_to_file(file)
        finally:
            file.close()
        # Update the timestamp
        self.timestamp = vfs.get_mtime(self.uri)


    def save_state_to(self, uri):
        file = vfs.make_file(uri)
        try:
            self.save_state_to_file(file)
        finally:
            file.close()


    def save_state_to_file(self, file):
        # We call "to_str" so this method will be good for sub-classes
        data = self.to_str()
        # Write and truncate (calls to "_save_state" must be done with the
        # pointer pointing to the beginning)
        file.write(data)
        file.truncate()


    #########################################################################
    # API
    #########################################################################
    def to_str(self):
        return self.data


    def set_data(self, data):
        self.set_changed()
        self.data = data


register_handler_class(File)
