# -*- coding: UTF-8 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import mimetypes
import os

# Import from itools
from domains import Domain, DomainAware, register_domain, get_domain
from mo import MO
from po import PO


__all__ = [
    'Domain',
    'DomainAware',
    'register_domain',
    'get_domain',
    'MO',
    'PO']


mimetypes.add_type('text/x-po', '.po')
mimetypes.add_type('application/x-mo', '.mo')

# Register the itools domain
path = os.path.join(os.path.split(globals()['__path__'][0])[0], 'locale')
register_domain('itools', path)
