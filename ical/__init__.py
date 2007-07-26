# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Deram  <nderam@gmail.com>
# Copyright (C) 2005 Nicolas Oyez  <nicoyez@gmail.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
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

"""
This module offers an API to handle calendaring and scheduling
resources in standard type iCalendar specified in the RFC 2445
(http://www.faqs.org/rfcs/rfc2445.html).
"""

# Import from itools
from gridlayout import get_grid_data
from icalendar import icalendar, PropertyValue
from types import DateTime

__all__ = [
    # Functions
    'get_grid_data',
    # DataTypes
    'DateTime',
    # Handlers
    'PropertyValue',
    'icalendar']
