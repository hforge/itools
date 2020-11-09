# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007, 2009-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
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

"""The purpose of this package is to implement URIs (Uniform Resource
Identifiers) as specified by RFC2396.
"""

# Import from itools
import mailto
from generic import Path, Reference, decode_query, encode_query
from generic import normalize_path
from uri import get_reference, get_uri_name, get_uri_path
from uri import resolve_uri, resolve_uri2, resolve_name
from uri import get_host_from_authority
from registry import register_scheme, get_scheme



__all__ = [
    'Path',
    'Reference',
    'decode_query',
    'encode_query',
    'register_scheme',
    'get_scheme',
    'normalize_path',
    # New functional API
    'get_reference',
    'resolve_uri',
    'resolve_uri2',
    'resolve_name',
    'get_uri_name',
    'get_uri_path',
    'get_host_from_authority',
    'mailto'
    ]
