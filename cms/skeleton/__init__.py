# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Luis Belmar-Letelier <luis@itaapy.com>
#               2006 Hervé Cauwelier <herve@itaapy.com>
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA

# Import from itools
from itools import get_abspath, get_version
from itools.gettext import domains

# Import from our package
import skins
from root import Root
import metadata
import folder
import document


# Make the product version available to Python code
__version__ = get_version(globals())

# Register domain (i18n)
path = get_abspath(globals(), 'locale')
domains.register_domain('example', path)
