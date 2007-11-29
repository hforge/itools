# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from itools
import file

_file_systems = {}


def register_file_system(name, fs_handler):
    _file_systems[name] = fs_handler


def deregister_file_system(name):
    if name in _file_systems:
        del _file_systems[name]


def get_file_system(name):
    # 'c' means Windows' "c:\" and is a filesystem
    if len(name) == 1:
        return file.FileFS
    if name not in _file_systems:
        raise NotImplementedError
    return _file_systems[name]
