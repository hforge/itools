# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2008-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from os import devnull, dup2, fork, open as os_open, O_RDWR, setsid
from resource import getrusage, RUSAGE_SELF
from sys import exit, stdin, stdout, stderr



def vmsize():
    """Returns the resident size in bytes.
    """
    rss = getrusage(RUSAGE_SELF).ru_maxrss
    return rss * 1024


def get_time_spent(mode='both', since=0.0):
    """Return the time spent by the current process in seconds.

    mode user -> time in user mode
    mode system -> time in system mode
    mode both -> time in user mode + time in system mode
    """
    data = getrusage(RUSAGE_SELF)

    if mode == 'system':
        return data.ru_stime - since
    elif mode == 'user':
        return data.ru_utime - since

    # Both
    return data.ru_stime + data.ru_utime - since


def become_daemon():
    try:
        pid = fork()
    except OSError:
        print 'unable to fork'
        exit(1)

    if pid == 0:
        # Daemonize
        setsid()
        # We redirect only the 3 first descriptors
        file_desc = os_open(devnull, O_RDWR)
        stdin.close()
        dup2(file_desc, 0)
        stdout.flush()
        dup2(file_desc, 1)
        stderr.flush()
        dup2(file_desc, 2)
    else:
        exit()

