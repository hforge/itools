# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from Python
from urlparse import urlsplit

# Import from itools
from itools import uri
import file
import http


def get_resource(reference):
    """
    From a uri reference returns a resource. Supported schemes:

    - file (the default)

    - http (only file resources, no language negotiation)
    """
    if not isinstance(reference, uri.Reference):
        reference = uri.get_reference(reference)

    if reference.scheme:
        scheme = reference.scheme
    else:
        scheme = 'file'

    if scheme == 'file':
        # reference must be a path
        return file.get_resource(reference.path)
    elif scheme == 'http':
        return http.get_resource(reference)
    else:
        raise ValueError, 'scheme "%s" unsupported' % scheme
