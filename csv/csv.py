# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


###########################################################################
# Index & Search
###########################################################################

class Index(dict):

    def _normalise_word(self, word):
        # XXX temporary until we analyse as the catalog does
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



class Catalog(object):

    __slots__ = ['indexes', 'analysers']

    def __init__(self):
        self.indexes = {}
        self.analysers = {}


    def add_index(self, name, analyser_name):
        self.indexes[name] = Index()
        self.analysers[name] = analysers.get_analyser(analyser_name)


    def index_document(self, document, number):
        for name in self.indexes:
            index = self.indexes[name]
            analyser = self.analysers[name]

            value = document.get_value(name)
            for word, position in analyser(value):
                index.setdefault(word, {})
                index[word].setdefault(number, [])
                index[word][number].append(position)


    def unindex_document(self, document, number):
        for name in self.indexes:
            index = self.indexes[name]
            analyser = self.analysers[name]

            value = document.get_value(name)
            for word, position in analyser(value):
                del index[word][number]


###########################################################################
# Handler
###########################################################################
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



class CSV(Text):

    class_mimetypes = ['text/comma-separated-values', 'text/csv']
    class_extension = 'csv'
    class_version = '20040625'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'lines', 'n_lines', 'catalog']

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
    # Load & Save
    #########################################################################
    def new(self, **kw):
        self.lines = []
        self.n_lines = 0
        # Initialize the catalog if needed (Index&Search)
        if self.schema is None:
            self.catalog = None
        else:
            self.catalog = Catalog()
            for column in self.columns:
                datatype = self.schema[column]
                index = getattr(datatype, 'index', None)
                if index is not None:
                    self.catalog.add_index(column, index)


    def _load_state_from_file(self, file):
        # Initialize
        self.new()

        # Read the data, and find out the encoding
        data = file.read()
        self.encoding = self.guess_encoding(data)

        schema = self.schema
        if schema is None:
            for line in parse(data):
                row = [ unicode(x, self.encoding) for x in line ]
                self._add_row(row)
        else:
            columns = self.columns
            for line in parse(data, len(columns)):
                row = [ schema[columns[i]].decode(value)
                        for i, value in enumerate(line) ]
                self._add_row(row)


    def to_str(self, encoding='UTF-8'):
        lines = []
        # When schema or columns (or both) are None there is plain 
        # string to string conversion
        schema = self.schema
        columns = self.columns
        if schema and columns:
            datatypes = [ (i, schema[x]) for i, x in enumerate(columns) ]
            for row in self.get_rows():
                line = []
                for i, datatype in datatypes:
                    try:
                        data = datatype.encode(row[i], encoding=encoding)
                    except TypeError:
                        data = datatype.encode(row[i])
                    line.append('"%s"' % data.replace('"', '""'))
                lines.append(','.join(line))
        else:
            for row in self.get_rows():
                line = [ '"%s"' % x.encode(encoding).replace('"', '""')
                         for x in row ]
                lines.append(','.join(line))
        return '\n'.join(lines)


    #########################################################################
    # Traverse
    #########################################################################
    def _get_virtual_handler(self, segment):
        index = int(segment.name)
        try:
            row = self.lines[index]
        except IndexError:
            raise LookupError
        if row is None:
            raise LookupError
        return row


    #########################################################################
    # API / Private
    #########################################################################
    def get_index(self, name):
        if self.schema is None:
            raise ValueError, 'schema not defined'

        if name not in self.schema:
            raise ValueError, 'the field "%s" is not defined' % name

        try:
            return self.catalog.indexes[name]
        except KeyError:
            raise ValueError, 'the field "%s" is not indexed' % name


    def _add_row(self, row):
        """Append new row as an instance of row class."""
        # Build the row
        row = self.row_class(row)
        row.number = self.n_lines
        row.columns = self.columns
        # Add
        self.lines.append(row)
        self.n_lines += 1
        # Index
        if self.schema is not None:
            self.catalog.index_document(row, row.number)


    #########################################################################
    # API / Public
    #########################################################################
    def is_indexed(self):
        """Check if at least one index is available for searching, etc."""
        if self.catalog is None:
            return False
        return bool(self.catalog.indexes)


    def get_nrows(self):
        return len([ x for x in self.lines if x is not None])


    def get_row(self, number):
        """
        Return row at the given line number. Count begins at 0.

        Raise an exception (IndexError) if the row is not available.
        XXX Maybe it should be better to return None.
        """
        row = self.lines[number]
        if row is None:
            raise IndexError, 'list index out of range'
        return row


    def get_rows(self, numbers=None):
        """
        Return rows at the given list of line numbers. If no numbers
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
        """Append new row as an instance of row class."""
        self.set_changed()
        self._add_row(row)


    def del_row(self, number):
        """Delete row at the given line number. Count begins at 0."""
        self.set_changed()

        # Remove
        row = self.lines[number]
        if row is None:
            raise IndexError, 'list assignment index out of range'
        self.lines[number] = None

        # Unindex
        if self.schema is not None:
            self.catalog.unindex_document(row, row.number)


    def del_rows(self, numbers):
        """Delete rows at the given line numbers. Count begins at 0."""
        self.set_changed()
        # Indexes are changing while deleting process
        for i in numbers:
            self.del_row(i)


    def search(self, query=None, **kw):
        """Return list of row numbers returned by executing the query."""
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
        return set([ x.get_value(name) for x in self.get_rows() ])


register_handler_class(CSV)
