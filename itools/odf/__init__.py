# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007, 2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
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
from .odf import ODFFile, ODTFile, ODPFile, ODSFile
from .oo import SXWFile, SXCFile, SXIFile
from . import schema


__all__ = [
    'schema',
    # Opend Document Format
    'ODFFile',
    'ODTFile',
    'ODPFile',
    'ODSFile',
    # Open Office 1.0
    'SXWFile',
    'SXCFile',
    'SXIFile',
    ]
