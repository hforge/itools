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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from copy import deepcopy
from cStringIO import StringIO
import datetime

# Import from itools
from itools.vfs import api as vfs
from itools.handlers.registry import register_handler_class
from base import Handler



class File(Handler):
    """
    This is the base handler class for any file handler. It is also used
    as the default handler class for any file resource that has not a more
    specific handler.
    """

    class_resource_type = 'file'


    __slots__ = ['resource', 'timestamp', 'data']


    def new(self, data=''):
        self.data = data


    #########################################################################
    # Load / Save
    #########################################################################
    def load_state(self):
        with vfs.open(self.uri, 'r') as file:
            self.load_state_from_file(file)
        self.timestamp = vfs.get_mtime(self.uri)


    def load_state_from(self, uri):
        file = vfs.open(uri)
        get_transaction().add(self)
        with file:
            self.load_state_from_file(file)
        self.timestamp = datetime.now()


    def load_state_from_file(self, file):
        self.data = file.read()


    def load_state_from_string(self, string):
        file = StringIO(string)


    def save_state(self):
        with vfs.open(self.uri, 'w') as file:
            self.save_state_to_file(file)


    def save_state_to(self, uri):
        with vfs.make_file(uri) as file:
            self.save_state_to_file(file)


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
