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
from signal import signal, SIGINT, SIG_IGN
from subprocess import call, Popen, PIPE


# Contants.  The commands the sub-process accepts.
CMD_CALL = 0
CMD_READ = 1
CMD_STOP = 2


def start_subprocess(path):
    """This methods starts another process that will be used to make
    questions to git.  This is done so because we fork to call the git
    commands, and using an specific process for this purpose minimizes
    memory usage (because fork duplicates the memory).
    """
    # Make the pipe that will connect the parent to the sub-process
    parent_pipe, child_pipe = Pipe()
    # Make and start the sub-process
    p = Process(target=subprocess, args=(path, child_pipe))
    p.start()
    # Return the pipe to the sub-process
    return parent_pipe



def subprocess(cwd, conn):
    signal(SIGINT, SIG_IGN)
    while conn.poll(None):
        # Recv
        command, data = conn.recv()
        # Action
        # FIXME Error handling
        if command == CMD_CALL:
            results = call(data, stdout=PIPE, stderr=PIPE, cwd=cwd)
        elif command == CMD_READ:
            popen = Popen(data, stdout=PIPE, stderr=PIPE, cwd=cwd)
            errno = popen.wait()
            if errno:
                results = errno, popen.stderr.read()
            else:
                results = errno, popen.stdout.read()
        elif command == CMD_STOP:
            conn.send(None)
            break
        else:
            results = None
        # Send
        conn.send(results)

