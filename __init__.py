# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2005 Luis Arturo Belmar-Letelier <luis@itaapy.com>
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
from utils import get_version, get_abspath
from gettext import register_domain


__version__ = get_version()

# Register the itools domain
path = get_abspath('locale')
register_domain('itools', path)
