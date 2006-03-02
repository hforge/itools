# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#                    2005 Piotr Macuk <piotr@macuk.pl>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import csv as python_csv

# Import from itools
from itools.handlers.Text import Text
from itools.catalog import Query



class Row(list):

    def __getattr__(self, name):
        try:
            index = self.columns.index(name)
        except ValueError:
            message = "'%s' object has no attribute '%s'"
            raise AttributeError, message % (self.__class__.__name__, name)

        return self[index]


class Index(dict):

    def search_word(self, word):
        if word in self:
            return self[word].copy()
        return {}



class CSV(Text):

    class_mimetypes = ['text/comma-separated-values', 'text/csv']
    class_extension = 'csv'
    class_version = '20040625'


    # Hash with column names and its types
    # Example: {'firstname': Unicode, 'lastname': Unicode, 'age': Integer}
    # To index some columns the schema should be declared as:
    # schema = {'firstname': Unicode, 'lastname': Unicode, 
    #           'age': Integer(index=True)}
    schema = None

    # List of the schema column names
    # Example: ['firstname', 'lastname', 'age']
    columns = None

    # The class to use for each row (this allows easy specialization)
    row_class = Row

    #########################################################################
    # Parsing
    #########################################################################
    def _get_csv_reader(self, data):
        """Build and return the csv file reader."""
        lines = data.splitlines()
        dialect = python_csv.Sniffer().sniff('\n'.join(lines[:10]))
        # Fix the fucking sniffer
        dialect.doublequote = True
        if dialect.delimiter == '':
            dialect.delimiter = ','
        return python_csv.reader(lines, dialect)


    def _parse(self, data):
        """Parse the csv data"""
        reader = self._get_csv_reader(data)
        # Only if the schema and columns are set, else the schema or
        # columns definition is ignored (schema is hash now and has no order)
        if self.is_schema_defined():
            for line in reader:
                decoded_line = self._decode_line(line)
                yield decoded_line
        else:
            encoding = Text.guess_encoding(data)
            for line in reader:
                yield [ unicode(x, encoding) for x in line ]


    def _decode_line(self, line):
        """Decode values from the csv line according to the schema."""
        return [ self.schema[self.columns[i]].decode(value) 
                 for i, value in enumerate(line) ]


    def _index_init(self):
        """Initialize csv values index list"""
        if self.state.indexes is None:
            self.state.indexes = [ None for i in self.columns ]


    def _index_all(self):
        """Index parsed lines from the csv data according to the schema. 
           The index keys are decoded data.
        """
        self._index_init()
        row_index = 0
        for line in self.state.lines:
            self._index_row(line, row_index)
            row_index = row_index + 1


    def _index_row(self, row, row_index):
        """Index one line"""
        indexes = self.state.indexes
        for i, value in enumerate(row):
            datatype = self.schema[self.columns[i]]
            if getattr(datatype, 'index', False) is True:
                if indexes[i] is None:
                    indexes[i] = Index()
                index = indexes[i]
                # XXX We should parse the value with itools.catalog.Analysers
                # and store the positions instead of an empty list, as
                # itools.catalog does.
                index.setdefault(value, {})
                index[value][row_index] = []


    def _unindex_row(self, row_index):
        """Unindex deleted row"""
        # XXX We should un-index directly looking from the row values, as
        # the commented code below shows. The difficulty comes from the
        # fact that row indexes change when a row before is deleted; in
        # other words, when we remove a row, we must re-index all rows
        # after. The solution is to use internal ids, different from the
        # row number, which don't change through the handler's live.
##        indexes = self.state.indexes
##        for i, value in enumerate(row):
##            index = indexes[i]
##            if index is not None:
##                del index[value][row_index]

        indexes = self.state.indexes
        for reverse_index in indexes:
            if reverse_index is not None:
                for key in reverse_index.keys():
                    idx = reverse_index[key]
                    # Remove deleted row index
                    try:
                        del idx[row_index]
                    except KeyError:
                        pass
                    if idx:
                        # Reindex remaining row indexes
                        new_idx = {}
                        for j in idx:
                            if j > row_index:
                                j = j - 1
                            new_idx[j] = {}
                        reverse_index[key] = new_idx
                    else:
                        del reverse_index[key]


    def _load_state(self, resource):
        data = resource.read()

        # Collection of None and reverse indexes.
        # When the column is indexed there will be dictionary with 
        # value: list of row indexes 
        # When there is no index associate with column, the None value
        # is placed into self.indexes list at the non indexed column position.
        # Example (with above indexed schema): [None, None, <reverse index>] 
        self.state.indexes = None

        lines = []
        index = 0
        for line in self._parse(data):
            row = self.row_class(line)
            row.index = index
            row.columns = self.columns
            lines.append(row)
            index = index + 1

        self.state.lines = lines
        self.state.encoding = self.guess_encoding(data)

        if self.is_schema_defined():
            # Index lines data
            self._index_all()


    # XXX This can't work until the virtual handler overhaul is done
##    def _get_virtual_handler(self, segment):
##        index = int(segment.name)
##        return self.state.lines[index]


    def get_index(self, name):
        if name not in self.schema:
            raise ValueError, 'the field "%s" is not defined' % name

        datatype = self.schema[name]
        if getattr(datatype, 'index', False) is False:
            raise ValueError, 'the field "%s" is not indexed' % name

        return self.state.indexes[self.columns.index(name)]


    #########################################################################
    # API
    #########################################################################
    def to_str(self, encoding='UTF-8'):
        lines = []
        # When schema or columns (or both) are None there is plain 
        # string to string conversion
        if self.schema and self.columns:
            for line in self.state.lines:
                line = [ '"%s"' % self.schema[self.columns[i]].encode(value) 
                         for i, value in enumerate(line) ]
                lines.append(','.join(line))
        else:
            for line in self.state.lines:
                line = [ '"%s"' % x.encode(encoding) for x in line ]
                lines.append(','.join(line))
        return '\n'.join(lines)


    def is_schema_defined(self):
        """Check if the handler schema is defined. Returns True of False"""
        if self.schema and self.columns:
            return True
        else:
            return False


    def get_nrows(self):
        return len(self.state.lines)


    def get_row(self, index):
        """Return row indexed by index.

           index -- number
        """
        return self.state.lines[index]


    def get_rows(self, indexes=None):
        """Return rows indexed by indexex.
           If indexes is not set (default None) the all rows 
           are returned.

           indexes -- list or tuple of numbers
        """
        if indexes is None:
            return self.state.lines

        rows = []
        for i in indexes:
            rows.append(self.state.lines[i])
        return rows


    def add_row(self, row):
        """Append new row.
           
           row -- list with new row values
        """
        self.set_changed()
        new_row = self.row_class(row)
        self.state.lines.append(new_row)

        if self.is_schema_defined():
            # Index the new line
            self._index_init()
            self._index_row(new_row, len(self.state.lines) - 1)


    def del_row(self, index):
        """Delete row indexed by index.

           index -- number
        """
        self.set_changed()
        row = self.state.lines[index]
        del self.state.lines[index]

        if self.is_schema_defined():
            # Unindex deleted row
            self._index_init()
            self._unindex_row(index)


    def del_rows(self, indexes):
        """Delete rows indexed by indexes.
           
           indexes -- list or tuple of numbers
        """
        self.set_changed()
        # Indexes are changing while deleting process
        index_offset = 0
        for i in indexes:
            self.del_row(i + index_offset)
            index_offset = index_offset - 1


    def search(self, query=None, **kw):
        """Return list of row indexes returned by executing the query.
        """
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(Query.Equal(key, value))

                query = Query.And(*atoms)
            else:
                raise ValueError, "expected a query"

        documents = query.search(self)
        # Sort by weight
        documents = documents.keys()
        documents.sort()

        return documents


Text.register_handler_class(CSV)
