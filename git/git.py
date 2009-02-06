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
from subprocess import Popen, PIPE

# Import from itools
from itools.core import freeze


def get_pipe(command, cwd=None):
    popen = Popen(command, stdout=PIPE, stderr=PIPE, cwd=cwd)
    errno = popen.wait()
    if errno:
        strerror = popen.stderr.read()
        raise EnvironmentError, (errno, strerror)
    return popen.stdout


def is_available():
    """Returns True if we are in a git working directory, False otherwise.
    """
    pipe = get_pipe(['git', 'branch'])
    return bool(pipe.read())


def get_filenames():
    """Returns the list of filenames tracked by git.
    """
    if not is_available():
        return []

    pipe = get_pipe(['git', 'ls-files'])
    return [ x.strip() for x in pipe.readlines() ]


def get_metadata(reference='HEAD', cwd=None):
    """Returns some metadata about the given commit reference.

    For now only the commit id and the timestamp are returned.
    """
    pipe = get_pipe(['git', 'cat-file', 'commit', reference], cwd=cwd)
    lines = pipe.readlines()

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
    metadata['message'] = ''.join(metadata['message'])

    # Ok
    return metadata



def get_branch_name():
    """Returns the name of the current branch.
    """
    pipe = get_pipe(['git', 'branch'])
    for line in pipe.readlines():
        if line.startswith('*'):
            return line[2:-1]

    return None


def get_tag_names():
    """Returns the names of all the tags.
    """
    pipe = get_pipe(['git', 'ls-remote', '--tags', '.'])
    return [ x.strip().split('/')[-1] for x in pipe.readlines() ]



def get_revisions(files=freeze([]), cwd=None):
    command = ['git', 'rev-list', 'HEAD', '--'] + files
    pipe = get_pipe(command, cwd=cwd)

    return [ x.rstrip() for x in pipe.readlines() ]



def get_diff(reference='HEAD', cwd=None):
    pipe = get_pipe(['git', 'show', reference, '--pretty=format:'], cwd=cwd)
    return [ x.rstrip() for x in pipe.readlines() ]
