# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
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

# Import from the Standard Library
from mimetypes import add_type

# Import from itools
from csv_ import CSVFile, Row
from parser import parse
from table import Table, Record, Property, UniqueError
from table import parse_table, fold_line, escape_data, is_multilingual


__all__ = [
    # Functions
    'parse',
    # Classes
    'CSVFile',
    'Row',
    # The Table handler (a kind of CSV on steroids)
    'Table',
    'Record',
    'Property',
    'UniqueError',
    'parse_table',
    'fold_line',
    'escape_data',
    'is_multilingual',
    ]



add_type('text/comma-separated-values', '.csv')
