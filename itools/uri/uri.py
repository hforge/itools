# Copyright (C) 2005-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006 Nicolas Deram <nderam@gmail.com>
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

import functools

# Import from itools
from .generic import GenericDataType
from .registry import get_scheme


@functools.lru_cache
def get_reference(reference):
    """Returns a URI reference of the good type from the given string.
    """
    if ':' in reference:
        scheme_name, scheme_specifics = reference.split(':', 1)
        scheme = get_scheme(scheme_name)
    else:
        scheme = GenericDataType

    return scheme.decode(reference)


def get_uri_name(uri):
    uri = get_reference(uri)

    return str(uri.path[-1])


def get_uri_path(uri):
    uri = get_reference(uri)

    return str(uri.path)


def get_host_from_authority(auth):
    """Get the host from the authority.  The format of the authority is:

      [userinfo@]host[:port]
    """
    return auth.split('@', 1)[-1].split(':', 1)[0]


def resolve_uri(base, reference):
    base = get_reference(base)
    reference = get_reference(reference)

    uri = base.resolve(reference)
    return str(uri)


def resolve_uri2(base, reference):
    base = get_reference(base)
    reference = get_reference(reference)

    uri = base.resolve2(reference)
    return str(uri)


def resolve_name(base, name):
    base = get_reference(base)

    uri = base.resolve_name(name)
    return str(uri)

