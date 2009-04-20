# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from multiprocessing import Process, Pipe
from subprocess import call, PIPE

# Import from itools
from git import get_diff, get_revisions_metadata


# The git process
GIT_STOP = 0
GIT_CALL = 1
GIT_REVISIONS = 2
GIT_DIFF = 3


def start_git_process(path):
    """This methods starts another process that will be used to make
    questions to git.  This is done so because we fork to call the git
    commands, and using an specific process for this purpose minimizes
    memory usage (because fork duplicates the memory).
    """
    # Make the pipe that will connect the parent to the git sub-process
    parent_pipe, child_pipe = Pipe()
    # Make and start the sub-process
    p = Process(target=git_process, args=(path, child_pipe))
    p.start()
    # Return the pipe to the git sub-process
    return parent_pipe



def git_process(cwd, conn):
    while conn.poll(None):
        # Recv
        command, data = conn.recv()
        # Action
        # FIXME Error handling
        if command == GIT_CALL:
            results = call(data, cwd=cwd, stdout=PIPE, stderr=PIPE)
        elif command == GIT_REVISIONS:
            results = get_revisions_metadata(data, cwd=cwd)
        elif command == GIT_DIFF:
            results = get_diff(data, cwd=cwd)
        elif command == GIT_STOP:
            conn.send(None)
            break
        else:
            results = None
        # Send
        conn.send(results)

