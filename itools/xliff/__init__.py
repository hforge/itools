# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from itools.core import add_type, get_abspath
from itools.xml import register_dtd
from .xliff import XLFFile, XLFUnit, XLFNote, File


__all__ = ['XLFFile', 'XLFUnit', 'XLFNote', 'File']


# Register mime type
add_type('application/x-xliff', '.xlf')

# Register DTD
# -//XLIFF//DTD XLIFF//EN
register_dtd(get_abspath('xliff.dtd'),
             urn='urn:publicid:-:XLIFF:DTD+XLIFF:EN')

