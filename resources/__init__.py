# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


# Import from Python
import os
from urlparse import urlsplit

# Import from itools
from itools.uri import get_reference
from itools.uri.generic import Reference, decode as uri_decode
import file
import http


def get_resource(reference):
    """
    From a uri reference returns a resource. Supported schemes:

    - file (the default)

    - http (only file resources, no language negotiation)
    """
    if not isinstance(reference, Reference):
        # Make it working with Windows
        if os.path.sep == '\\':
            if len(reference) > 1 and reference[1] == ':':
                reference = 'file://%s' % reference
        reference = get_reference(reference)

    base = os.getcwd()
    # Make it working with Windows
    if os.path.sep == '\\':
        # Internally we use always the "/"
        base = base.replace(os.path.sep, '/')

    base = uri_decode('file://%s/' % base)
    reference = base.resolve(reference)

    scheme = reference.scheme

    if scheme == 'file':
        # reference must be a path
        return file.get_resource(reference)
    elif scheme == 'http':
        return http.get_resource(reference)

    raise ValueError, 'scheme "%s" unsupported' % scheme
