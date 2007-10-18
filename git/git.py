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

# Import from the Standard Library
from os import popen


def is_available():
    """Returns True if we are in a git working directory, False otherwise.
    """
    return bool(popen('git-branch').read())


def get_filenames():
    """Returns the list of filenames tracked by git.
    """
    if not git_is_available():
        return []

    return [ x.strip() for x in popen('git-ls-files').readlines() ]


def get_metadata(reference='HEAD'):
    """Returns some metadata about the given commit reference.

    For now only the commit id and the timestamp are returned.
    """
    lines = popen('git-cat-file commit %s' % reference).readlines()
    # The commit id
    commit_id = lines[0].strip().split()[1]
    # The author
    for line in lines:
        if line.startswith('author'):
            author = line
            break
    else:
        raise ValueError, ("cannot find the commit author, "
            "please report the output of 'git-cat-file commit %s'" % reference)
    # The timestamp
    timestamp = datetime.fromtimestamp(int(author.strip().split()[-2]))

    return commit_id, timestamp


def get_branch_name():
    """Returns the name of the current branch.
    """
    for line in popen('git-branch').readlines():
        if line.startswith('*'):
            return line[2:-1]

    return None


def get_tag_names():
    """Returns the names of all the tags.
    """
    cmd = 'git-ls-remote -t .'
    return [ x.strip().split('/')[-1] for x in popen(cmd).readlines() ]


