# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2008, 2010, 2012 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
# Copyright (C) 2006-2007, 2009-2010 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007 Nicolas Deram <nderam@gmail.com>
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
from itools.datatypes import String, Unicode
from itools.handlers import TextFile, guess_encoding, register_handler_class
from .parser import parse


# TODO Drop the 'Row' class, use a list or a tuple instead.
# Row.get_value(name) will be replaced by CSVFile.get_value(row, name)
class Row(list):

    def get_value(self, name):
        if self.columns is None:
            column = int(name)
        else:
            column = self.columns.index(name)

        return self[column]

    def copy(self):
        clone = self.__class__(self)
        clone.number = self.number
        clone.columns = self.columns
        return clone


class CSVFile(TextFile):

    class_mimetypes = ['text/comma-separated-values', 'text/x-comma-separated-values',
                       'text/csv', 'text/x-csv',
                       'application/csv', 'application/x-csv']
    class_extension = 'csv'

    # Hash with column names and its types
    # Example: {'firstname': Unicode, 'lastname': Unicode, 'age': Integer}
    schema = None

    # List of the schema column names
    # Example: ['firstname', 'lastname', 'age']
    columns = None

    # Parsing options
    class_csv_guess = False
    has_header = False
    skip_header = False

    #########################################################################
    # Load & Save
    #########################################################################
    def reset(self):
        self.header = None
        self.lines = []
        self.n_lines = 0

    def new(self):
        pass

    def _load_state_from_file(self, file):
        # Guess encoding
        data = file.read()
        self.encoding = guess_encoding(data)

        # Build the parser
        parser = parse(data, self.columns, self.schema, self.class_csv_guess,
                       self.has_header, self.encoding)

        # Header
        if self.has_header:
            self.header = next(parser)

        # Content
        for line in parser:
            self._add_row(line)

    def to_str(self, encoding='UTF-8', separator=',', newline='\n'):

        def escape(data):

            return '"%s"' % data.replace('"', '""')

        lines = []
        # Header
        if self.has_header:
            line = [escape(Unicode.encode(x, encoding)) for x in self.header]
            line = separator.join(line)
            lines.append(line)

        # When schema or columns (or both) are None there is plain
        # string to string conversion
        schema = self.schema
        columns = self.columns
        if schema and columns:
            datatypes = [(i, schema[x]) for i, x in enumerate(columns)]
            for row in self.get_rows():
                line = []
                for i, datatype in datatypes:
                    if isinstance(row[i], str):
                        line.append(escape(row[i]))
                    else:
                        try:
                            data = datatype.encode(row[i], encoding=encoding)
                        except TypeError:
                            data = datatype.encode(row[i])
                        line.append(escape(data))
                lines.append(separator.join(line))
        else:
            for row in self.get_rows():
                line = [escape(x) for x in row]
                lines.append(separator.join(line))
        return newline.join(lines)

    #########################################################################
    # API / Private
    #########################################################################
    def _add_row(self, row):
        """Append new row as an instance of row class.
        """
        # Build the row
        row = Row(row)
        row.number = self.n_lines
        row.columns = self.columns
        # Add
        self.lines.append(row)
        self.n_lines += 1

        return row

    def get_datatype(self, name):
        if self.schema is None:
            # Default
            return String
        return self.schema[name]

    #########################################################################
    # API / Public
    #########################################################################
    def get_nrows(self):
        return len([x for x in self.lines if x is not None])

    def get_row(self, number):
        """Return row at the given line number. Count begins at 0.

        Raise an exception (IndexError) if the row is not available.
        XXX Maybe it should be better to return None.
        """
        row = self.lines[number]
        if row is None:
            raise IndexError('list index out of range')
        return row

    def get_rows(self, numbers=None):
        """Return rows at the given list of line numbers. If no numbers
        are given, then all rows are returned.

        Count begins at 0.
        """
        if numbers is None:
            for row in self.lines:
                if row is not None:
                    yield row
        else:
            for i in numbers:
                yield self.get_row(i)

    def add_row(self, row):
        """Append new row as an instance of row class.
        """
        self.set_changed()
        return self._add_row(row)

    def update_row(self, index, **kw):
        row = self.get_row(index)
        self.set_changed()
        # Update
        columns = self.columns
        if columns is None:
            for name in kw:
                column = int(name)
                row[column] = kw[name]
        else:
            for name in kw:
                column = columns.index(name)
                row[column] = kw[name]

    def del_row(self, number):
        """Delete row at the given line number. Count begins at 0.
        """
        self.set_changed()

        # Remove
        row = self.lines[number]
        if row is None:
            raise IndexError('list assignment index out of range')
        self.lines[number] = None

    def del_rows(self, numbers):
        """Delete rows at the given line numbers. Count begins at 0.
        """
        self.set_changed()
        # Indexes are changing while deleting process
        for i in numbers:
            self.del_row(i)

    def get_unique_values(self, name):
        return set([x.get_value(name) for x in self.get_rows()])


register_handler_class(CSVFile)
