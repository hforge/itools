# -*- coding: UTF-8 -*-
# Copyright (C) ${YEAR} ${AUTHOR_NAME} <${AUTHOR_EMAIL}>
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
from itools import get_abspath, get_version
from itools.gettext import register_domain
from itools.cms.skins import register_skin

# Import from our package
from base import Handler
import metadata
from root import Root
from skins import FrontOffice1


# Make the product version available to Python code
__version__ = get_version(globals())


# Register the skin
path = get_abspath(globals(), 'ui/frontoffice1')
skin = FrontOffice1(path)
register_skin('frontoffice1', skin)

# Register domain (i18n)
path = get_abspath(globals(), 'locale')
register_domain(Handler.class_domain, path)
