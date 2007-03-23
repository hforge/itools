# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
import mailto
from generic import Path, Reference, Query, Authority
from uri import get_reference, get_absolute_reference, get_absolute_reference2
from registry import register_scheme, get_scheme



__all__ = [
    'Path',
    'Reference',
    'Query',
    'Authority',
    'get_reference',
    'get_absolute_reference',
    'get_absolute_reference2',
    'register_scheme',
    'get_scheme']
