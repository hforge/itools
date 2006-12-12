# -*- coding: UTF-8 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the future
from __future__ import absolute_import

# Import from the Standard Library
import csv as python_csv

# Import from itools
from itools.handlers.Text import Text
from itools.catalog import queries, analysers
from itools.handlers.registry import register_handler_class


###########################################################################
# Parsing
###########################################################################
sniffer = python_csv.Sniffer()

def parse(data, n_columns=None):
    """
    This method is a generator that returns one CSV row at a time.
    To do the job it wraps the standard Python's csv parser.
    """
    # Find out the dialect
    if data:
        lines = data.splitlines()
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



class Row(list):

    def get_value(self, name):
        if self.columns is None:
            raise ValueError, 'schema not defined'

        column = self.columns.index(name)
        return self[column]


    def set_value(self, name, value):
        if self.columns is None:
            raise ValueError, 'schema not defined'

        column = self.columns.index(name)
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

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'lines', 'indexes']


    def new(self, **kw):
        self.lines = []        
        if self.is_schema_defined():
            self._index_init()
        else:
            self.indexes = None


    # Hash with column names and its types
    # Example: {'firstname': Unicode, 'lastname': Unicode, 'age': Integer}
    # To index some columns the schema should be declared as:
    # schema = {'firstname': Unicode, 'lastname': Unicode, 
    #           'age': Integer(index='<analyser>')}
    # where <analyser> is an itools.catalog analyser or derivate: keyword,
    # book, text, path.
    schema = None

    # List of the schema column names
    # Example: ['firstname', 'lastname', 'age']
    columns = None

    # The class to use for each row (this allows easy specialization)
    row_class = Row


    #########################################################################
    # Parsing
    #########################################################################
    def _parse(self, data):
        """Parse the csv data"""
        # Only if the schema and columns are set, else the schema or
        # columns definition is ignored.
        if self.is_schema_defined():
            schema = self.schema
            columns = self.columns

            n_columns = len(columns)
            for line in parse(data, n_columns):
                yield [ schema[columns[i]].decode(value)
                        for i, value in enumerate(line) ]
        else:
            encoding = Text.guess_encoding(data)
            for line in parse(data):
                yield [ unicode(x, encoding) for x in line ]


    def _index_init(self):
        """Initialize csv values index list"""
        indexes = self.indexes = []
        for column in self.columns:
            datatype = self.schema[column]
            if getattr(datatype, 'index', None) is not None:
                indexes.append(Index())
            else:
                indexes.append(None)


    def _index_all(self):
        """Index parsed lines from the csv data according to the schema. 
           The index keys are decoded data.
        """
        self._index_init()
        for row_number, line in enumerate(self.lines):
            self._index_row(line, row_number)


    def _index_row(self, row, row_number):
        """Index one line"""
        indexes = self.indexes
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
##        indexes = self.indexes
##        for i, value in enumerate(row):
##            index = indexes[i]
##            if index is not None:
##                del index[value][row_number]

        indexes = self.indexes
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
                        # decrease row numbers above the deleted row
                        new_idx = {}
                        for number in idx:
                            if number > row_number:
                                new_number = number - 1
                            else:
                                new_number = number
                            new_idx[new_number] = idx[number]
                        reverse_index[key] = new_idx
                    else:
                        del reverse_index[key]


    def _load_state_from_file(self, file):
        data = file.read()

        # Collection of None and reverse indexes.
        # When the column is indexed there will be dictionary with 
        # value: list of row indexes 
        # When there is no index associate with column, the None value
        # is placed into self.indexes list at the non indexed column position.
        # Example (with above indexed schema): [None, None, <reverse index>] 
        self.indexes = None

        lines = []
        for row_number, line in enumerate(self._parse(data)):
            row = self.row_class(line)
            row.number = row_number
            row.columns = self.columns
            lines.append(row)

        self.lines = lines
        self.encoding = self.guess_encoding(data)

        if self.is_schema_defined():
            # Index lines data
            self._index_all()


    # XXX This can't work until the virtual handler overhaul is done
    def _get_virtual_handler(self, segment):
        index = int(segment.name)
        return self.lines[index]


    #########################################################################
    # Catalog API
    def get_index(self, name):
        if name not in self.schema:
            raise ValueError, 'the field "%s" is not defined' % name

        datatype = self.schema[name]
        if getattr(datatype, 'index', False) is False:
            raise ValueError, 'the field "%s" is not indexed' % name

        return self.indexes[self.columns.index(name)]


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
            for row in self.lines:
                line = [ '"%s"' % datatype.encode(row[i]).replace('"', '""')
                         for i, datatype in datatypes ]
                lines.append(','.join(line))
        else:
            for line in self.lines:
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


    def is_indexed(self):
        """Check if at least one index is available for searching, etc."""
        indexes = self.indexes
        if indexes is None:
            return False
        indexes = [i for i in indexes if i is not None]
        if indexes:
            return True

        return False


    def get_nrows(self):
        return len(self.lines)


    def get_row(self, number):
        """Return row at the given line number.

        Count begins at 0.
        """
        return self.lines[number]


    def get_rows(self, numbers=None):
        """Return rows at the given list of line numbers.
           If no numbers are given, then all rows are returned.

        Count begins at 0.
        """
        if numbers is None:
            for row in self.lines:
                yield row
        else:
            for i in numbers:
                yield self.lines[i]


    def add_row(self, row):
        """Append new row as an instance of row class."""
        self.set_changed()
        new_row = self.row_class(row)
        number = self.get_nrows()
        new_row.number = number
        new_row.columns = self.columns
        self.lines.append(new_row)

        if self.is_schema_defined():
            # Index the new line
            self._index_row(new_row, number)


    def del_row(self, number):
        """Delete row at the given line number.

        Count begins at 0.
        """
        self.set_changed()
        row = self.lines[number]
        del self.lines[number]

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
        if not self.is_indexed():
            raise IndexError, 'no index is defined in the schema'

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


    def get_unique_values(self, name):
        return set([ x.get_value(name) for x in self.lines ])


register_handler_class(CSV)
