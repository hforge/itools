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

# Import from other modules
from win32api import OpenProcess, TerminateProcess


def is_pid_running(pid):
    """Returns true if there is a process with the given pid working.
    """
    try:
        OpenProcess(1, False, pid)
    except:
        return False
    return True



def kill(pid):
    handle = OpenProcess(1, 0, pid)
    TerminateProcess(handle, 0)
