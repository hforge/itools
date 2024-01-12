# Copyright (C) 2005-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007-2008 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
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
from .base import DataType
from .primitive import Boolean, Decimal, Email, Integer, String, Unicode
from .primitive import Tokens, MultiLinesTokens, Enumerate
from .primitive import PathDataType, URI
from .primitive import QName, XMLAttribute, XMLContent
from .datetime_ import ISOCalendarDate, ISOTime, ISODateTime, HTTPDate
from .languages import LanguageTag
# Define alias Date, Time and DateTime (use ISO standard)
from .datetime_ import ISOCalendarDate as Date, ISOTime as Time
from .datetime_ import ISODateTime as DateTime


__all__ = [
    # Abstract class
    'DataType',
    # DataTypes
    'Integer',
    'Decimal',
    'Unicode',
    'String',
    'Boolean',
    'Email',
    'PathDataType',
    'URI',
    'QName',
    'Tokens',
    'MultiLinesTokens',
    'Enumerate',
    'XMLContent',
    'XMLAttribute',
    'ISOCalendarDate',
    'ISOTime',
    'ISODateTime',
    'HTTPDate',
    'LanguageTag',
    # Aliases
    'Date',
    'Time',
    'DateTime']
