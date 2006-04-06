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

# Import from the Standard Library
import datetime

# Import from itools
from itools.resources import memory
from Handler import Handler
from itools.handlers.registry import register_handler_class



class File(Handler):
    """
    This is the base handler class for any file handler. It is also used
    as the default handler class for any file resource that has not a more
    specific handler.
    """

    class_resource_type = 'file'


    def new(self, data=''):
        self.data = data


    def _load_state(self, resource):
        # Be lazy
        self.data = None


    def _save_state(self, resource):
        resource.write(self.to_str())
        resource.truncate()


    #########################################################################
    # Lazy load
    def _load_data(self):
        resource = self.resource
        resource.open()
        self.data = resource.read()
        resource.close()


    #########################################################################
    # API
    #########################################################################
    def to_str(self):
        return self.data


    def set_data(self, data):
        self.set_changed()
        self.data = data


    def copy_handler(self):
        resource = memory.File(self.to_str())
        return self.__class__(resource)



register_handler_class(File)
