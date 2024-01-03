# -*- coding: UTF-8 -*-
# Copyright (C) 2008-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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
from sys import platform

# Import from itools
from .cache import LRUCache
from .freeze import freeze, frozendict, frozenlist
from .lazy import lazy
from .mimetypes_ import add_type, guess_all_extensions, guess_extension
from .mimetypes_ import guess_type, has_encoding, has_extension
from .prototypes import prototype_type, prototype, is_prototype
from .prototypes import proto_property, proto_lazy_property
from .timezones import fixed_offset, local_tz
from .utils import get_abspath, merge_dicts, get_sizeof, get_pipe, get_version


if platform[:3] == 'win':
    from ._win import become_daemon, fork, get_time_spent, vmsize
else:
    from ._unix import become_daemon, fork, get_time_spent, vmsize


__all__ = [
    # Thingies are cool
    'prototype_type',
    'prototype',
    'is_prototype',
    'proto_property',
    'proto_lazy_property',
    # Frozen types
    'freeze',
    'frozendict',
    'frozenlist',
    # Lazy load
    'lazy',
    # Caching
    'LRUCache',
    # Mimetypes
    'add_type',
    'guess_all_extensions',
    'guess_extension',
    'guess_type',
    'has_encoding',
    'has_extension',
    # Time
    'fixed_offset',
    'local_tz',
    # Utility functions
    'get_abspath',
    'get_version',
    'merge_dicts',
    'get_sizeof',
    'get_pipe',
    # System specific functions
    'become_daemon',
    'fork',
    'get_time_spent',
    'vmsize',
   ]
