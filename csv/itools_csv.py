# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#                    2005 Piotr Macuk <piotr@macuk.pl>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import csv as python_csv

# Import from itools
from itools.handlers.Text import Text
from itools.catalog import queries, analysers



class Row(list):

    def __getattr__(self, name):
        message = "'%s' object has no attribute '%s'"
        if self.columns is None:
            raise AttributeError, message % (self.__class__.__name__, name)

        try:
            column = self.columns.index(name)
        except ValueError:
            raise AttributeError, message % (self.__class__.__name__, name)

        return self[column]


    def __setattr__(self, name, value):
        if name in ('number', 'columns', 'parent', 'name'):
            list.__setattr__(self, name, value)
        else:
            try:
                column = self.columns.index(name)
            except ValueError:
                message = "'%s' object has no attribute '%s'"
                raise AttributeError, message % (self.__class__.__name__, name)

            self[column] = value


    def copy(self):
        clone = self.__class__(self)
        clone.number = self.number
        clone.columns = self.columns

        return clone



class Index(dict):

    def _normalise_word(self, word):
        # XXX temporary until we analyse as the catalog do
        if isinstance(word, bool):
            word = unicode(int(word))
        elif not isinstance(word, basestring):
            word = unicode(word)
        elif isinstance(word, unicode):
            word = word.lower()

        return word


    def search_word(self, word):
        word = self._normalise_word(word)

        if word in self:
            return self[word].copy()
        
        return {}


    def search_range(self, left, right):
        left = self._normalise_word(left)
        right = self._normalise_word(right)

        rows = {}
        
        if not left:
            for key in self.keys():
                if  key < right:
                    for number in self[key]:
                        rows[number] = rows.get(number, 0) + 1
        elif not right:
            for key in self.keys():
                if left <= key:
                    for number in self[key]:
                        rows[number] = rows.get(number, 0) + 1
        else:
            for key in self.keys():
                if left <= key < right:
                    for number in self[key]:
                        rows[number] = rows.get(number, 0) + 1

        return rows



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

    # Internal parser value
    # Number of columns in parsed file
    __number_of_columns = 0

    # Internal parser value
    # Number of currently parsed line
    __curr_parsed_line_no = 0

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
                self._syntax_check(line)
                decoded_line = self._decode_line(line)
                yield decoded_line
        else:
            encoding = Text.guess_encoding(data)
            for line in reader:
                self._syntax_check(line)
                yield [ unicode(x, encoding) for x in line ]


    def _syntax_check(self, line):
        """Syntax check of the parsed line"""
        if self.__curr_parsed_line_no == 0:
            if self.is_schema_defined():
                self.__number_of_columns = len(self.columns)
            else:
                self.__number_of_columns = len(line)
        self.__curr_parsed_line_no += 1
        if len(line) != self.__number_of_columns:
            msg = 'CSV file syntax error: wrong number of columns at line %d'
            raise ValueError, msg % self.__curr_parsed_line_no


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
        for row_number, line in enumerate(self.state.lines):
            self._index_row(line, row_number)


    def _index_row(self, row, row_number):
        """Index one line"""
        indexes = self.state.indexes
        for i, value in enumerate(row):
            datatype = self.schema[self.columns[i]]
            analyser_name = getattr(datatype, 'index', None)
            if analyser_name is None:
                continue
            analyser = analysers.get_analyser(analyser_name)
            if indexes[i] is None:
                indexes[i] = Index()
            index = indexes[i]
            for word, position in analyser(value):
                index.setdefault(word, {})
                index[word].setdefault(row_number, [])
                index[word][row_number].append(position)


    def _unindex_row(self, row_number):
        """Unindex deleted row"""
        # XXX We should un-index directly looking from the row values, as
        # the commented code below shows. The difficulty comes from the
        # fact that row numbers change when a row before is deleted; in
        # other words, when we remove a row, we must re-index all rows
        # after. The solution is to use internal ids, different from the
        # row number, which don't change through the handler's live.
##        indexes = self.state.indexes
##        for i, value in enumerate(row):
##            index = indexes[i]
##            if index is not None:
##                del index[value][row_number]

        indexes = self.state.indexes
        for reverse_index in indexes:
            if reverse_index is not None:
                for key in reverse_index.keys():
                    idx = reverse_index[key]
                    # Remove deleted row index
                    try:
                        del idx[row_number]
                    except KeyError:
                        pass
                    if idx:
                        # Reindex remaining row indexes
                        new_idx = {}
                        for j in idx:
                            if j > row_number:
                                j = j - 1
                            new_idx[j] = idx[j]
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
        for row_number, line in enumerate(self._parse(data)):
            row = self.row_class(line)
            row.number = row_number
            row.columns = self.columns
            lines.append(row)

        self.state.lines = lines
        self.state.encoding = self.guess_encoding(data)

        if self.is_schema_defined():
            # Index lines data
            self._index_all()


    # XXX This can't work until the virtual handler overhaul is done
    def _get_virtual_handler(self, segment):
        index = int(segment.name)
        return self.state.lines[index]


    #########################################################################
    # Catalog API
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
        schema = self.schema
        columns = self.columns
        if schema and columns:
            datatypes = [ (i, schema[x]) for i, x in enumerate(columns) ]
            for row in self.state.lines:
                line = [ '"%s"' % datatype.encode(row[i]).replace('"', '""')
                         for i, datatype in datatypes ]
                lines.append(','.join(line))
        else:
            for line in self.state.lines:
                line = [ '"%s"' % x.encode(encoding).replace('"', '""')
                         for x in line ]
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


    def get_row(self, number):
        """Return row at the given line number.

        Count begins at 0.
        """
        return self.state.lines[number]


    def get_rows(self, numbers=None):
        """Return rows at the given list of line numbers.
           If no numbers are given, then all rows are returned.

        Count begins at 0.
        """
        if numbers is None:
            for row in self.state.lines:
                yield row
        else:
            for i in numbers:
                yield self.state.lines[i]


    def add_row(self, row):
        """Append new row as an instance of row class."""
        self.set_changed()
        new_row = self.row_class(row)
        number = self.get_nrows()
        new_row.number = number
        new_row.columns = self.columns
        self.state.lines.append(new_row)

        if self.is_schema_defined():
            # Index the new line
            self._index_row(new_row, number)


    def del_row(self, number):
        """Delete row at the given line number.

        Count begins at 0.
        """
        self.set_changed()
        row = self.state.lines[number]
        del self.state.lines[number]

        if self.is_schema_defined():
            # Unindex deleted row
            self._unindex_row(number)


    def del_rows(self, numbers):
        """Delete rows at the given line numbers.
           
        Count begins at 0.
        """
        self.set_changed()
        # Indexes are changing while deleting process
        number_offset = 0
        for i in numbers:
            self.del_row(i + number_offset)
            number_offset = number_offset - 1


    def search(self, query=None, **kw):
        """Return list of row numbers returned by executing the query.
        """
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(queries.Equal(key, value))

                query = queries.And(*atoms)
            else:
                raise ValueError, "expected a query"

        documents = query.search(self)
        # Sort by weight
        documents = documents.keys()
        documents.sort()

        return documents


Text.register_handler_class(CSV)
