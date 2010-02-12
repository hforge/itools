# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2009 David Versmisse <david.versmisse@itaapy.com>
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
from base import READ, WRITE, READ_WRITE, APPEND
from filename import FileName
from lfs import lfs
from vfs import vfs

# Import from gio
from gio import Error



__all__ = [
    'lfs',
    'vfs',
    # Datatypes
    'FileName',
    # File modes
    'READ',
    'WRITE',
    'READ_WRITE',
    'APPEND',
    # Exceptions
    'Error']
