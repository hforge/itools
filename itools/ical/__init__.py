# Copyright (C) 2007 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2007-2008, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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
from .icalendar import iCalendar
from .datatypes import DateTime, Time

__all__ = [
    # DataTypes
    'DateTime',
    'Time',
    # Handlers
    'iCalendar']
