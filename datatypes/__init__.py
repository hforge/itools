# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from base import DataType
from primitive import (Integer, Decimal, Unicode, String, Boolean, Email, URI,
                       FileName, QName, Tokens, Enumerate, XML, XMLAttribute,
                       is_datatype)
from datetime_ import ISOCalendarDate, ISOTime, ISODateTime, InternetDateTime
# Define alias Date, Time and DateTime (use ISO standard)
from datetime_ import (ISOCalendarDate as Date, ISOTime as Time,
                       ISODateTime as DateTime)


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
    'URI',
    'FileName',
    'QName',
    'Tokens',
    'Enumerate',
    'XML',
    'XMLAttribute',
    'ISOCalendarDate',
    'ISOTime',
    'ISODateTime',
    'InternetDateTime',
    # Alias
    'Date',
    'Time',
    'DateTime']
