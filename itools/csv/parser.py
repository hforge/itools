# Copyright (C) 2006-2008, 2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2010 Hervé Cauwelier <herve@oursours.net>
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
from itools.datatypes import String, Unicode


sniffer = Sniffer()

def parse_line(reader, line, datatypes, encoding, n_columns):
    # Check column length
    if len(line) != n_columns:
        msg = 'CSV syntax error: wrong number of columns at line %d: %s'
        line_num = getattr(reader, 'line_num', None)
        raise ValueError(msg % (line_num, line))

    # Decode values
    decoded = []
    for i, datatype in datatypes:
        value = line[i]
        try:
            value = datatype.decode(value, encoding=encoding)
        except TypeError:
            value = datatype.decode(value)
        decoded.append(value)

    # Next line
    try:
        next_line = next(reader)
    except StopIteration:
        next_line = None
    except Exception:
        line_num = getattr(reader, 'line_num', None)
        raise ValueError(f'Cannot read line number {line_num}')

    # Ok
    return decoded, next_line


def parse(data, columns=None, schema=None, guess=False, has_header=False,
          encoding='UTF-8', **kw):
    """This method is a generator that returns one CSV row at a time.  To
    do the job it wraps the standard Python's csv parser.
    """
    if not data:
        return

    lines = data.splitlines(True)

    # 1. The reader, guess dialect if requested
    if guess is True:
        dialect = sniffer.sniff('\n'.join(lines[:10]))
        # Fix the sniffer
        dialect.doublequote = True
        if dialect.delimiter == '' or dialect.delimiter == ' ':
            dialect.delimiter = ','
        reader = read_csv(lines, dialect, **kw)
    else:
        reader = read_csv(lines, **kw)

    # 2. Find out the number of columns, if not specified
    line = next(reader)
    n_columns = len(columns) if columns is not None else len(line)

    # 3. The header
    if has_header is True:
        datatypes = [Unicode for x in range(n_columns)]
        datatypes = enumerate(datatypes)
        datatypes = list(datatypes)
        header, line = parse_line(reader, line, datatypes, encoding, n_columns)
        yield header

    # 4. The content
    if schema is not None:
        datatypes = [schema.get(c, String) for c in columns]
    else:
        datatypes = [String for x in range(n_columns)]
    datatypes = enumerate(datatypes)
    datatypes = list(datatypes)

    while line is not None:
        decoded, line = parse_line(reader, line, datatypes, encoding, n_columns)
        yield decoded
