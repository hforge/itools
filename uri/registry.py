# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2006 Juan David IbÃ¡Ã±ez Palomar <jdavid@itaapy.com>
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
from generic import GenericDataType


_schemes = {}


def register_scheme(name, handler):
    _schemes[name] = handler


def get_scheme(name):
    if name in _schemes:
        return _schemes[name]
    return GenericDataType
