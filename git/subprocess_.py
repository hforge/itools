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
from atexit import register
from errno import ENOEXEC
from multiprocessing import Process, Pipe
from os import chdir
from signal import signal, SIGINT, SIG_IGN
from subprocess import Popen, PIPE, CalledProcessError
from traceback import format_exc


# FIXME Not thread safe
subp = None
pipe_to_subprocess = None


def start_subprocess(path, pid_file=None):
    """This methods starts another process that will be used to make
    questions to git.  This is done so because we fork to call the git
    commands, and using an specific process for this purpose minimizes
    memory usage (because fork duplicates the memory).
    """
    global subp
    global pipe_to_subprocess
    if pipe_to_subprocess is None:
        # Make the pipe that will connect the parent to the sub-process
        pipe_to_subprocess, child_pipe = Pipe()
        # Make and start the sub-process
        subp = Process(target=subprocess, args=(path, child_pipe))
        subp.start()
        if pid_file is not None:
            open(pid_file, 'w').write(str(subp.pid))
        register(stop_subprocess)


def stop_subprocess():
    global subp
    global pipe_to_subprocess
    if subp:
        subp.terminate()
        subp = pipe_to_subprocess = None


def send_subprocess(command, wait=True, path=None):
    pipe_to_subprocess.send((path, command))
    if wait is True:
        return read_subprocess(command)


def read_subprocess(command=None):
    # An IOError exception may be raised if the process is interrupted
    errno, data = pipe_to_subprocess.recv()
    if errno:
        if command is not None:
            command = ' '.join(command)
        raise CalledProcessError(errno, command)
    return data


def subprocess(cwd, conn):
    chdir(cwd)
    signal(SIGINT, SIG_IGN)
    while conn.poll(None):
        path, data = conn.recv()
        # Spawn subprocess
        try:
            popen = Popen(data, stdout=PIPE, stderr=PIPE, cwd=path)
        except TypeError:
            err = format_exc()
            conn.send((ENOEXEC, err))
            continue

        # Communicate
        stdout, stderr = popen.communicate()
        errno = popen.returncode
        if errno:
            conn.send((errno, stderr))
        else:
            conn.send((errno, stdout))
