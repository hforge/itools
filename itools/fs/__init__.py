# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
# Copyright (C) 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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
from common import READ, WRITE, READ_WRITE, APPEND, FileName
from lfs import lfs
from vfs import vfs

# Import from gio
from gi.repository.GLib import GError



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
    'GError'
    ]
