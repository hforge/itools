# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from base import BaseFS
from datatypes import FileName
import file
import memfs
from registry import register_file_system, deregister_file_system
from vfs import can_read, can_write, copy, cwd, exists, get_atime, get_ctime
from vfs import get_mimetype, get_mtime, get_names, get_size, is_file
from vfs import is_folder, make_file, make_folder, move, open, remove
from vfs import traverse, READ, WRITE, READ_WRITE, APPEND


__all__ = [
    'cwd',
    'BaseFS',
    # Datatypes
    'FileName',
    # File modes
    'READ',
    'WRITE',
    'READ_WRITE',
    'APPEND',
    # Registry
    'register_file_system',
    'deregister_file_system',
    # Functions
    'exists',
    'is_file',
    'is_folder',
    'can_read',
    'can_write',
    'get_ctime',
    'get_mtime',
    'get_atime',
    'get_mimetype',
    'get_size',
    'make_file',
    'make_folder',
    'remove',
    'open',
    'copy',
    'move',
    'get_names',
    'traverse']

