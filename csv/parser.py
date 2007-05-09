# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the future
from __future__ import absolute_import

# Import from the Standard Library
import csv as python_csv


sniffer = python_csv.Sniffer()

def parse(data, n_columns=None):
    """
    This method is a generator that returns one CSV row at a time.
    To do the job it wraps the standard Python's csv parser.
    """
    # Find out the dialect
    if data:
        lines = data.splitlines(True)
        dialect = sniffer.sniff('\n'.join(lines[:10]))
        # Fix the fucking sniffer
        dialect.doublequote = True
        if dialect.delimiter == '':
            dialect.delimiter = ','
        # Get the reader
        reader = python_csv.reader(lines, dialect)
        # Find out the number of columns, if not specified
        if n_columns is None:
            line = reader.next()
            n_columns = len(line)
            yield line
        # Go
        for line in reader:
            if len(line) != n_columns:
                msg = u'CSV syntax error: wrong number of columns at line %d'
                raise ValueError, msg % reader.line_num
            yield line


