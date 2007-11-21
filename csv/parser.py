# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from csv import get_dialect, reader as read_csv, Sniffer

# Import from itools
from itools.datatypes import String


sniffer = Sniffer()


def parse(data, columns=None, schema=None, guess=True, **kw):
    """This method is a generator that returns one CSV row at a time.  To
    do the job it wraps the standard Python's csv parser.
    """
    # FIXME The parameter 'guess' should be False by default (explicit is
    # better)

    # Find out the dialect
    if data:
        lines = data.splitlines(True)
        # The dialect
        if guess is True:
            dialect = sniffer.sniff('\n'.join(lines[:10]))
            # Fix the fucking sniffer (FIXME To remove now we can make things
            # explicit, kept here for backwards compatibility).
            dialect.doublequote = True
            if dialect.delimiter == '' or dialect.delimiter == ' ':
                dialect.delimiter = ','
        else:
            # Default is Excel
            dialect = get_dialect('excel')
        # The low level parser (Python's csv)
        reader = read_csv(lines, dialect, **kw)

        # Find out the number of columns, if not specified
        if columns is not None:
            n_columns = len(columns)
        else:
            line = reader.next()
            n_columns = len(line)
            yield line
        # Go
        for line in reader:
            if len(line) != n_columns:
                msg = u'CSV syntax error: wrong number of columns at line %d'
                line = getattr(reader, 'line_num', None)
                if line is None:
                    # Python 2.4
                    msg = u'CSV syntax error: wrong number of columns'
                else:
                    # Python 2.5
                    msg = msg % line
                raise ValueError, msg
            if schema is not None:
                line = [ schema.get(columns[i], String).decode(value)
                         for i, value in enumerate(line) ]
            yield line


