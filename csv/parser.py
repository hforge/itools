# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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

# Import from the Standard Library
from csv import reader as read_csv, Sniffer

# Import from itools
from itools.datatypes import String


sniffer = Sniffer()


def parse(data, columns=None, schema=None, guess=False, encoding='UTF-8',
          **kw):
    """This method is a generator that returns one CSV row at a time.  To
    do the job it wraps the standard Python's csv parser.
    """
    # Find out the dialect
    if data:
        lines = data.splitlines(True)
        # The dialect
        if guess is True:
            dialect = sniffer.sniff('\n'.join(lines[:10]))
            # Fix the fucking sniffer
            dialect.doublequote = True
            if dialect.delimiter == '' or dialect.delimiter == ' ':
                dialect.delimiter = ','
            reader = read_csv(lines, dialect, **kw)
        else:
            reader = read_csv(lines, **kw)

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
                msg = (
                    'CSV syntax error: wrong number of columns at line %d: %s')
                line_num = getattr(reader, 'line_num', None)
                raise ValueError, msg % (line_num, line)
            if schema is not None:
                datatypes = [schema.get(c, String) for c in columns]
                decoded = []
                for i, datatype in enumerate(datatypes):
                    try:
                        value = datatype.decode(line[i], encoding=encoding)
                    except TypeError:
                        value = datatype.decode(line[i])
                    decoded.append(value)
                line = decoded
            yield line


