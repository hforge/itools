# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
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

"""This module provides file handlers for Open Office 1.0 documents
(Writer, Calc and Impress).
"""

# Import from itools
from itools.core import add_type
from itools.handlers import register_handler_class
from odf import OOFile


class SXWFile(OOFile):

    class_mimetypes = ['application/vnd.sun.xml.writer']
    class_extension = 'sxw'



class SXCFile(OOFile):

    class_mimetypes = ['application/vnd.sun.xml.calc']
    class_extension = 'sxc'



class SXIFile(OOFile):

    class_mimetypes = ['application/vnd.sun.xml.impress']
    class_extension = 'sxi'


# Register
add_type('application/vnd.sun.xml.writer', '.sxw')
add_type('application/vnd.sun.xml.calc', '.sxc')
add_type('application/vnd.sun.xml.impress', '.sxi')

for handler in [SXWFile, SXCFile, SXIFile]:
    register_handler_class(handler)
