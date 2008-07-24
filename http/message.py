# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.handlers import File
import headers


class Message(File):
    """
    Base class, for HTTP request and responses.
    """

    def set_header(self, name, value):
        name = name.lower()
        if isinstance(value, str):
            type = headers.get_type(name)
            value = type.decode(value)
        self.headers[name] = value


    def has_header(self, name):
        name = name.lower()
        return name in self.headers


    def get_header(self, name):
        name = name.lower()
        return self.headers.get(name)
