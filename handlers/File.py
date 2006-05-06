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

# Import from the Standard Library
import datetime

# Import from itools
from itools.resources import base, memory
from Handler import Handler, State



class File(Handler):
    """
    This is the base handler class for any file handler. It is also used
    as the default handler class for any file resource that has not a more
    specific handler.
    """

    class_resource_type = 'file'


    def __init__(self, resource=None, **kw):
        if resource is None:
            # No resource given, then we create a dummy one
            data = self.get_skeleton(**kw)
            resource = memory.File(data)

        self.resource = resource
        self.state = State()
        self.load_state()


    #########################################################################
    # Load / Save
    #########################################################################
    def _load_state(self, resource):
        state = self.state
        state.data = resource.read()


    def _save_state(self, resource):
        resource.truncate(0)
        resource.write(self.to_str())


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self):
        return ''


    #########################################################################
    # API
    #########################################################################
    def to_str(self):
        return self.state.data


    def set_data(self, data):
        self.set_changed()
        self.state.data = data


    def copy_handler(self):
        resource = memory.File(self.to_str())
        return self.__class__(resource)



Handler.register_handler_class(File)
