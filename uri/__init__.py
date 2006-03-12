# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
