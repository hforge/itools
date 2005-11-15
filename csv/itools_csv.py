# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import csv as python_csv
from types import StringType, TupleType, ListType

# Import from itools
from itools.handlers.Text import Text



class Row(list):
    pass



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


    #########################################################################
    # Parsing
    #########################################################################
    def _get_csv_reader(self, data):
        """Build and return the csv file reader."""
        dialect = python_csv.Sniffer().sniff('\n'.join(data.splitlines()[:10]))
        if dialect.delimiter == '':
            dialect.delimiter = ','
        return python_csv.reader(data.splitlines(), dialect)


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
        for i, value in enumerate(row):
            try:
                if self.schema[self.columns[i]].index == True:
                    if self.state.indexes[i] is None:
                        self.state.indexes[i] = {}
                    if self.state.indexes[i].has_key(value):
                        self.state.indexes[i][value].append(row_index)
                    else:
                        self.state.indexes[i][value] = [row_index]
            except:
                pass


    def _unindex_row(self, row_index):
        """Unindex deleted row"""
        for i, reverse_index in enumerate(self.state.indexes):
            if reverse_index is not None:
                for key in reverse_index.keys():
                    idx = self.state.indexes[i][key]
                    # Remove deleted row index
                    try:
                        idx.remove(row_index)
                    except ValueError:
                        pass
                    if idx == []:
                        del self.state.indexes[i][key]
                    else:
                        # Reindex remaining row indexes
                        idx1 = [j for j in idx if j < row_index]
                        idx2 = [j - 1 for j in idx if j > row_index]
                        self.state.indexes[i][key] = idx1 + idx2
    

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
            row = Row(line)
            row.index = index
            lines.append(row)
            index = index + 1

        self.state.lines = lines
        self.state.encoding = self.guess_encoding(data)

        if self.is_schema_defined():
            # Index lines data
            self._index_all()


    def _get_virtual_handler(self, segment):
        index = int(segment.name)
        return self.state.lines[index]


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
                line = [ '"%s"' % x for x in line ]
                lines.append(','.join(line))
        return '\n'.join(lines)

    
    def is_schema_defined(self):
        """Check if the handler schema is defined. Returns True of False"""
        if self.schema and self.columns:
            return True
        else:
            return False


    def get_row(self, index):
        """Return row indexed by index.

           index -- number
        """
        return self.state.lines[index]


    def get_rows(self, indexes):
        """Return rows indexed by indexex.

           indexes -- list or tuple of numbers
        """
        rows = []
        for i in indexes:
            rows.append(self.state.lines[i])
        return rows


    def add_row(self, row):
        """Append new row.
           
           row -- list with new row values
        """
        self.set_changed()
        new_row = Row(row)
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


    def get_all_rows(self):
        """Return all csv rows as list of the Row objects."""
        return self.state.lines


    def get_columns_by_names(self, columns):
        """Return only selected columns by its names (names in self.columns)
           
           columns -- tuple or list of column names
        """
        out = []
        for line in self.state.lines:
            out.append(Row([ line[self.columns.index(c)] for c in columns ]))
        return out

    
    def get_columns_by_indexes(self, columns):
        """Return only selected columns by numerical indexes
           
           columns -- tuple or list of numbers
        """
        out = []
        for line in self.state.lines:
            out.append(Row([ line[i] for i in columns ]))
        return out


    def search(self, column_name, value):
        """Return list of row indexes where the value is in the column_name
           or None when the index is not set for that column

           column_name -- string with column name where the value will be search
           value -- itools.datatypes object to search
        """
        if self.state.indexes is None:
            return None

        reverse_index = self.state.indexes[self.columns.index(column_name)]
        if reverse_index is None:
            return None

        if not reverse_index.has_key(value):
            return []
        else:
            return reverse_index[value]


    # And operator for lists used in advanced_search
    def _and(self, left, right):
        l = set(left)
        r = set(right)
        l.intersection_update(r)
        return list(l)


    # Or operator for lists used in advanced_search
    def _or(self, left, right):
        l = set(left)
        r = set(right)
        l.update(r)
        return list(l)


    def advanced_search(self, query):
        """Return list of row indexes after executing the query
           or None when one or more query items is None (query item
           is None when the query item column is not indexed).
           The query item can be: 
           - the (column_name, value) tuple 
           - the operator:  'or' or 'and'
           - the list of the previous advanced_search result.

           query -- list of query items for example:
           1) [('name', 'dde'), 'and', ('country', 'Sweden')]
           2) [('name', 'dde'), 'or', ('name', 'fse'), 
               'and', ('country', 'France')]
           3) [result1, 'and', result2, 'or', result3]
        """
        result = []
        operator = 'or'
        right = None
        for item in query:
            if type(item) is TupleType:
                right = self.search(item[0], item[1])
                # The column is not indexed -- return None
                if right is None: 
                    return None
            elif type(item) is ListType:
                right = item
            elif type(item) is StringType and item in ('and', 'or'):
                operator = item
                right = None

            if right is not None:
                if operator == 'and':
                    result = self._and(result, right)
                else:
                    result = self._or(result, right)

        return result
    


Text.register_handler_class(CSV)
