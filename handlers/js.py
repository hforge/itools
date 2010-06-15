# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from registry import register_handler_class
from text import TextFile




class JSFile(TextFile):

    class_mimetypes = ['application/x-javascript']
    class_extension = 'js'


    def get_units(self, srx_handler=None):
        raise NotImplementedError


    def translate(self, catalog, srx_handler=None):
        raise NotImplementedError


# Register
register_handler_class(JSFile)
