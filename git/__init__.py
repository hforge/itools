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
from daemon import start_git_process
from daemon import GIT_STOP, GIT_CALL, GIT_REVISIONS, GIT_DIFF
from git import is_available, get_filenames, get_metadata, get_branch_name
from git import get_revisions, get_tag_names, get_diff
from git import get_revisions_metadata



__all__ = [
    'get_branch_name',
    'get_diff',
    'get_filenames',
    'get_metadata',
    'get_revisions',
    'get_revisions_metadata',
    'get_tag_names',
    'is_available',
    # Sub-process
    'start_git_daemon',
    'GIT_STOP',
    'GIT_CALL',
    'GIT_REVISIONS',
    'GIT_DIFF',
    ]
