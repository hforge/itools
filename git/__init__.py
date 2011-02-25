# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from git import describe, get_branch_name, get_filenames, get_metadata
from git import is_available
from subprocess_ import start_subprocess

try:
    from _libgit import WorkTree
except ImportError:
    from _git import WorkTree



__all__ = [
    'describe',
    'get_branch_name',
    'get_filenames',
    'get_metadata',
    'is_available',
    # New API (uses libgit2 if available)
    'start_subprocess',
    'WorkTree',
    ]
