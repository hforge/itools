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
try:
    from win32api import OpenProcess
    from win32con import PROCESS_QUERY_INFORMATION, PROCESS_VM_READ
    from win32process import GetProcessTimes, GetProcessMemoryInfo
except ImportError:
    print 'Warning: win32 is not installed'



def get_win32_handle(pid):
    """Return the windows handle for a pid.
    """
    mask = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
    return OpenProcess(mask, False, pid)


def get_time_spent(mode='both', since=0.0):
    """Return the time spent by the current process in microseconds:

    mode user -> time in user mode
    mode system -> time in system mode
    mode both -> time in user mode + time in system mode
    """
    handle = get_win32_handle(getpid())
    data = GetProcessTimes(handle)
    if mode == 'system':
        return data['KernelTime'] / 10000000.0 - since
    elif mode == 'user':
        return data['UserTime'] / 10000000.0 - since

    # Both
    return (data['KernelTime'] + data['UserTime']) / 10000000.0 - since



def vmsize(scale={'kB': 1024.0, 'mB': 1024.0*1024.0,
                  'KB': 1024.0, 'MB': 1024.0*1024.0}):
    handle = get_win32_handle(getpid())
    m = GetProcessMemoryInfo(handle)
    return m["WorkingSetSize"]



def become_daemon():
    raise NotImplementedError, 'become_daemon not yet implemented for Windows'



def fork():
    raise NotImplementedError, 'fork not yet implemented for Windows'

