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
from datetime import datetime

# Import from itools
from itools.core import freeze, get_pipe


def is_available():
    """Returns True if we are in a git working directory, False otherwise.
    """
    try:
        data = get_pipe(['git', 'branch'])
    except EnvironmentError:
        return False
    return bool(data)


def get_filenames():
    """Returns the list of filenames tracked by git.
    """
    data = get_pipe(['git', 'ls-files'])
    return [ x.strip() for x in data.splitlines() ]


def get_metadata(reference='HEAD', cwd=None):
    """Returns some metadata about the given commit reference.

    For now only the commit id and the timestamp are returned.
    """
    data = get_pipe(['git', 'cat-file', 'commit', reference], cwd=cwd)
    lines = data.splitlines()

    # Default values
    metadata = {
        'tree': None,
        'parent': None,
        'author': (None, None),
        'committer': (None, None),
        'message': []}

    # Parse the data (with a simple automaton)
    state = 0
    for line in lines:
        if state == 0:
            # Heading
            line = line.strip()
            if not line:
                state = 1
                continue
            key, value = line.split(' ', 1)
            if key == 'tree':
                metadata['tree'] = value
            elif key == 'parent':
                metadata['parent'] = value
            elif key == 'author':
                name, ts, tz = value.rsplit(' ', 2)
                ts = datetime.fromtimestamp(int(ts))
                metadata['author'] = (name, ts)
            elif key == 'committer':
                name, ts, tz = value.rsplit(' ', 2)
                ts = datetime.fromtimestamp(int(ts))
                metadata['committer'] = (name, ts)
        else:
            # Message
            metadata['message'].append(line)

    # Post-process message
    metadata['message'] = '\n'.join(metadata['message'])

    # Ok
    return metadata



def get_branch_name():
    """Returns the name of the current branch.
    """
    data = get_pipe(['git', 'branch'])
    for line in data.splitlines():
        if line.startswith('*'):
            return line[2:]

    return None



def describe(match=None):
    # The command
    command = ['git', 'describe', '--tags', '--long']
    if match:
        command.extend(['--match', match])

    # Call
    try:
        data = get_pipe(command)
    except EnvironmentError:
        return None
    tag, n, commit = data.split('-')
    return tag, int(n), commit



def get_revisions(files=freeze([]), cwd=None):
    command = ['git', 'rev-list', 'HEAD', '--'] + files
    data = get_pipe(command, cwd=cwd)

    return [ x.rstrip() for x in data.splitlines() ]

