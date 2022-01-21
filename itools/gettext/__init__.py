# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008 Sylvain Taverne <taverne.sylvain@gmail.com>
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

# Import from itools
from itools.core import add_type, get_abspath
from .domains import register_domain, get_domain, MSG, get_language_msg
from .mo import MOFile
from .po import POFile, POUnit, encode_source


__all__ = [
    'encode_source',
    'register_domain',
    'get_domain',
    'MSG',
    'MOFile',
    'POFile',
    'POUnit',
    # Utility functions
    'get_language_msg',
    ]


add_type('text/x-gettext-translation', '.po')
add_type('text/x-gettext-translation-template', '.pot')
add_type('application/x-gettext-translation', '.mo')
add_type('application/x-gettext-translation', '.gmo')

# Register the itools domain
path = get_abspath('../locale')
register_domain('itools', path)
