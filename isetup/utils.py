# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os.path import exists
from sys import _getframe

# Import from itools
from itools.core import get_abspath


def get_version(mname=None):
    if mname is None:
        mname = _getframe(1).f_globals.get('__name__')

    path = get_abspath('version.txt', mname=mname)
    if exists(path):
        return open(path).read().strip()
    return None


