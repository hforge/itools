# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from itools
import mailto
import generic
from generic import Path, Reference


schemes = {'mailto': mailto}


def get_reference(reference):
    """
    Factory that returns an instance of the right scheme.
    """
    if ':' in reference:
        scheme_name, scheme_specifics = reference.split(':', 1)
        if scheme_name in schemes:
            scheme = schemes[scheme_name]
            return scheme.decode(scheme_specifics)

    return generic.decode(reference)
