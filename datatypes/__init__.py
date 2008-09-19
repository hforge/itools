# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007-2008 Hervé Cauwelier <herve@itaapy.com>
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
from base import DataType, is_datatype
from primitive import Boolean, Decimal, Email, Integer, String, Unicode
from primitive import Tokens, MultiLinesTokens, Enumerate, DynamicEnumerate
from primitive import PathDataType, URI
from primitive import QName, XMLAttribute, XMLContent
from datetime_ import ISOCalendarDate, ISOTime, ISODateTime, HTTPDate
from languages import LanguageTag
# Define alias Date, Time and DateTime (use ISO standard)
from datetime_ import ISOCalendarDate as Date, ISOTime as Time
from datetime_ import ISODateTime as DateTime


__all__ = [
    # Abstract clases
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
    'DynamicEnumerate',
    'XMLContent',
    'XMLAttribute',
    'ISOCalendarDate',
    'ISOTime',
    'ISODateTime',
    'HTTPDate',
    'LanguageTag',
    # Alias
    'Date',
    'Time',
    'DateTime']
