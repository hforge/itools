# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os import getpid
import resource

# Import from itools
import git


def vmsize(scale={'kB': 1024.0, 'mB': 1024.0*1024.0,
                  'KB': 1024.0, 'MB': 1024.0*1024.0}):
    status = '/proc/%d/status' % getpid()
    status = open(status).read()
    i = status.index('VmSize:')
    status = status[i:].split(None, 3)  # whitespace
    # convert Vm value to bytes
    return float(status[1]) * scale[status[2]]

def get_time_spent(mode='both', since=0.0):
    """
    Return the time spent by the current process in SECONDS

    mode user -> time in user mode
    mode system -> time in system mode
    mode both -> time in user mode + time in system mode
    """

    data = resource.getrusage(resource.RUSAGE_SELF)

    if mode == 'system':
        return data[1] - since
    elif mode == 'user':
        return data[0] - since
    else:
        # both
        return data[0] + data[1] - since
