# Copyright (C) 2004, 2006-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 Nicolas Deram <nderam@gmail.com>
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
from itools.core import add_type
from .csv_ import CSVFile, Row
from .parser import parse
from .table import Table, Record, UniqueError
from .table import parse_table, fold_line, escape_data, is_multilingual
from .table import Property, property_to_str, deserialize_parameters


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
    'property_to_str',
    'UniqueError',
    'parse_table',
    'fold_line',
    'escape_data',
    'is_multilingual',
    'deserialize_parameters',
    ]


add_type('text/comma-separated-values', '.csv')
