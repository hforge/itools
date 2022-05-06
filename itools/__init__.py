# -*- coding: UTF-8 -*-
# Copyright (C) 2004, 2006, 2008-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
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

# Import from standard lib
from logging import getLogger, NullHandler

getLogger("itools.core").addHandler(NullHandler())
getLogger("itools.web").addHandler(NullHandler())
getLogger("itools.database").addHandler(NullHandler())
getLogger("itools.stl").addHandler(NullHandler())
getLogger("itools.catalog").addHandler(NullHandler())

# The version
__version__ = "0.80.2"
__version_info__ = tuple(
    int(num) if num.isdigit() else num
    for num in __version__.replace("-", ".", 1).split(".")
)
