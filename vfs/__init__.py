# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from file import FileFS
from registry import register_file_system
from vfs import (cwd, exists, is_file, is_folder, can_read, can_write,
                 get_ctime, get_mtime, get_atime, get_mimetype, get_size,
                 make_file, make_folder, remove, open, copy, move, get_names,
                 traverse, READ, WRITE, APPEND)


__all__ = [
    'cwd',
    'BaseFS',
    'FileFS',
    # File modes
    'READ',
    'WRITE',
    'APPEND',
    # Registry
    'register_file_system',
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


