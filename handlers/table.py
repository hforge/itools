# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Nicolas Deram <nderam@itaapy.com>
#               2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.vfs import vfs
from itools.datatypes import DateTime, String
from itools.catalog import MemoryCatalog, PhraseQuery, AndQuery, get_field
from file import File


###########################################################################
# Parser
###########################################################################
def unfold_lines(data):
    """
    Unfold the folded lines.
    """
    i = 0
    lines = data.splitlines()

    line = ''
    while i < len(lines):
        next = lines[i]
        if next.startswith(' ') or next.startswith('\t'):
            line += next[1:]
        else:
            if line:
                yield line
            line = next
        i += 1
    if line:
        yield line


def read_name(line):
    """
    Reads the property name from the line. Returns the name and the
    rest of the line:

        name
        [parameters]value
    """
    c, lexeme = line[0], ''
    # Test first character of name
    if not c.isalnum() and c != '-':
        raise SyntaxError, 'unexpected character (%s)' % c
    # Test if line contains ':'
    if not ':' in line:
        raise SyntaxError, 'character (:) must appear at least one time'
    # Cut name
    while not c in (';', ':'):
        line = line[1:]
        if c.isalnum() or c in ['-', '_']:
            lexeme += c
        else:
            raise SyntaxError, "unexpected character '%s' (%s)" % (c, ord(c))
        c = line[0]

    return lexeme, line


# Manage an icalendar content line value property [with parameters] :
#
#   *(;param-name=param-value1[, param-value2, ...]) : value CRLF
  

# Lexical & syntaxic analysis
#   status :
#     1 --> parameter begun (just after ';')
#     2 --> param-name begun 
#     3 --> param-name ended, param-value beginning
#     4 --> param-value quoted begun (just after '"')
#     5 --> param-value NOT quoted begun 
#     6 --> param-value ended (just after '"' for quoted ones)
#     7 --> value to begin (just after ':')
#     8 --> value begun 

# Tokens
TPARAM, TVALUE = range(2)
token_name = ['name', 'parameter', 'value']


def get_tokens(property):
    status, lexeme, last = 0, '', ''

    # Init status
    c, property = property[0], property[1:]
    if c == ';':
        status = 1
    elif c == ':':
        status = 7
        
    for c in property:
        # parameter begun (just after ';')
        if status == 1:
            if c.isalnum() or c in ('-'):
                lexeme, status = c, 2
            else:
                raise SyntaxError, 'unexpected character (%s) at status %s'\
                                    % (c, status)

        # param-name begun 
        elif status == 2:
            if c.isalnum() or c in ('-'):
                lexeme += c
            elif c == '=':
                lexeme += c
                status = 3
            else:
                raise SyntaxError, 'unexpected character (%s) at status %s'\
                                    % (c, status)

        # param-name ended, param-value beginning
        elif status == 3:
            if c == '"':
                lexeme += c
                status = 4
            elif c in (';',':',',') :
                raise SyntaxError, 'unexpected character (%s) at status %s'\
                                    % (c, status)
            else:    
                lexeme += c
                status = 5

        # param-value quoted begun (just after '"')
        elif status == 4:
            if c == '"':
                lexeme += c
                status = 6
            else:
                lexeme += c

        # param-value NOT quoted begun 
        elif status == 5:
            if c in (':',';',',') :
                status = 6
            elif c=='"':
                raise SyntaxError, 'unexpected character (%s) at status %s'\
                                    % (c, status)
            else:    
                lexeme += c

        # value to begin (just after ':')
        elif status == 7:
            lexeme, status = c, 8

        # value begun 
        elif status == 8:
            lexeme += c

        # param-value ended (just after '"' for quoted ones)
        if status == 6:
            if c == ':':
                status = 7
                yield TPARAM, lexeme
            elif c == ';': 
                status = 1
                yield TPARAM, lexeme
            elif c == ',': 
                lexeme += c
                status = 3
            elif c == '"':
                if last == '"':
                    raise SyntaxError, 'unexpected repeated character (%s)'\
                          ' at status %s' % (c, status)
                last = '"'
            else:
                raise SyntaxError, 'unexpected character (%s) at status %s'\
                                    % (c, status)

    if status not in (7, 8):
        raise SyntaxError, 'unexpected property (%s)' % property

    yield TVALUE, lexeme



def parse_table(data):
    """
    This is the public interface of the module "itools.ical.parser", a
    low-level parser of iCalendar files.

    The input is the data to be parsed (a byte strings), the output
    is a sequence of tuples:

        name, value {param_name: param_value}

    Where all the elements ('name', 'value', 'param_name' and 'param_value')
    are byte strings.
    """
    for line in unfold_lines(data):
        parameters = {}
        name, line = read_name(line)
        # Read the parameters and the property value
        for token, lexeme in get_tokens(line):
            if token == TPARAM:
                param_name, param_value = lexeme.split('=')
                parameters[param_name] = param_value.split(',')
            elif token == TVALUE:
                # Unescape special characters
                # TODO Check the spec
                value = [ x.replace("\\r", "\r").replace("\\n", "\n")
                          for x in lexeme.split('\\\\') ]
                value = '\\'.join(value)
            else:
                raise SyntaxError, 'unexpected %s' % token_name[token]
        yield name, value, parameters




###########################################################################
# File Handler
###########################################################################
class Property(object):

    __slots__ = ['value', 'parameters']

    def __init__(self, value, parameters={}):
        self.value = value
        self.parameters = parameters



class Record(list):

    __slots__ = ['id']


    def __init__(self, id):
        self.id = id


    def __getattr__(self, name):
        version = self[-1]
        if name not in version:
            raise AttributeError, "'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name)

        property = version[name]
        if isinstance(property, list):
            return [ x.value for x in property ]
        return property.value


    def get_property(self, name):
        version = self[-1]
        if name in version:
            return version[name]

        return None


    # For indexing purposes
    def get_value(self, name):
        version = self[-1]
        if name not in version:
            return None

        property = version[name]
        if isinstance(property, list):
            return [ x.value for x in property ]
        return property.value



class Table(File):
    
    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'records', 'catalog', 'added_records', 'removed_records']


    #######################################################################
    # Hash with field names and its types
    # Example: {'firstname': Unicode, 'lastname': Unicode, 'age': Integer}
    # To index some fields the schema should be declared as:
    # schema = {'firstname': Unicode, 'lastname': Unicode, 
    #           'age': Integer(index='<analyser>')}
    # where <analyser> is an itools.catalog analyser or derivate: keyword,
    # book, text, path.
    #######################################################################
    schema = {}

    def get_datatype(self, name):
        if name == 'ts':
            return DateTime(multiple=False)
        if name in self.schema:
            return self.schema[name]
        return String(multiple=True)


    #######################################################################
    # Handlers
    #######################################################################
    def new(self):
        self.records = []
        self.added_records = []
        self.removed_records = []
        # The catalog (for index and search)
        self.catalog = MemoryCatalog()
        for name, datatype in self.schema.items():
            index = getattr(datatype, 'index', None)
            if index is not None:
                self.catalog.add_index(name, index)


    def _load_state_from_file(self, file):
        self.new()
        # Load the records
        records = self.records
        n = 0
        version = None
        for name, value, parameters in parse_table(file.read()):
            if name == 'id':
                version = {}
                # Identifier and Sequence (id)
                uid, seq = value.split('/')
                # Record
                uid = int(uid)
                if uid >= n:
                    # New record
                    records.extend([None] * (uid - n))
                    record = Record(uid)
                    records.append(record)
                    n = uid + 1
                else:
                    # Get the record
                    record = records[uid]
                # Version
                if seq == 'DELETED':
                    # Deleted
                    records[uid] = None
                    record = None
                else:
                    seq = int(seq)
                    if seq > len(record):
                        msg = 'unexpected sequence "%s" for record "%s"'
                        raise ValueError, msg % (seq, uid)
                    record.append(version)
                continue
            # Timestamp (ts), Schema, or Something else
            datatype = self.get_datatype(name)
            value = datatype.decode(value)
            property = Property(value, parameters)
            if getattr(datatype, 'multiple', False) is True:
                version.setdefault(name, []).append(property)
            elif name in version:
                raise ValueError, "property '%s' can occur only once" % name
            else:
                version[name] = property
        # Index the records
        for record in records:
            if record is not None:
                self.catalog.index_document(record, record.id)


    def _version_to_str(self, id, seq, version):
        lines = ['id:%d/%d\n' % (id, seq)]
        names = version.keys()
        names.sort()
        for name in names:
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                properties = version[name]
            else:
                properties = [version[name]]
            for property in properties:
                if property.value is None:
                    continue
                lines.append(name)
                pnames = property.parameters.keys()
                pnames.sort()
                for pname in pnames:
                    pvalues = property.parameters[pname]
                    pvalues = ','.join(pvalues)
                    lines.append(';%s=%s' % (pname, pvalues))
                value = datatype.encode(property.value)
                lines.append(':%s\n' % value)
        lines.append('\n')
        return ''.join(lines)


    def to_str(self):
        lines = []
        id = 0
        for record in self.records:
            if record is not None:
                seq = 0
                for version in record:
                    version = self._version_to_str(id, seq, version)
                    lines.append(version)
                    seq += 1
            # Next
            id += 1

        return ''.join(lines)


    #######################################################################
    # Save (use append for scalability)
    #######################################################################
    def save_state(self):
        with vfs.open(self.uri, 'a') as file:
            # Added records
            for id, seq in self.added_records:
                version = self.records[id][seq]
                version = self._version_to_str(id, seq, version)
                file.write(version)
            self.added_records = []
            # Removed records
            for id, ts in self.removed_records:
                file.write('id:%s/DELETED\n' % id)
                file.write('ts:%s\n' % DateTime.encode(ts))
                file.write('\n')
            self.removed_records = []

        # Update the timestamp
        self.timestamp = vfs.get_mtime(self.uri)


    #######################################################################
    # API / Private
    #######################################################################
    def get_analyser(self, name):
        datatype = self.get_datatype(name)
        return get_field(datatype.index)


    def get_index(self, name):
        if name not in self.schema:
            raise ValueError, 'the field "%s" is not defined' % name

        if name not in self.catalog.indexes:
            raise ValueError, 'the field "%s" is not indexed' % name

        return self.catalog.indexes[name]


    #######################################################################
    # API / Public
    #######################################################################
    def get_record(self, id, sequence=-1):
        if id >= len(self.records):
            return None
        return self.records[id]


    def add_record(self, kw):
        id = len(self.records)
        record = Record(id)
        version = {}
        # Fix the type
        for name, value in kw.items():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                value = [ x if isinstance(x, Property) else Property(x)
                          for x in value ]
            elif not isinstance(value, Property):
                value = Property(value)
            version[name] = value
        version['ts'] = Property(datetime.now())
        record.append(version)
        # Change
        self.set_changed()
        self.added_records.append((id, 0))
        self.records.append(record)
        self.catalog.index_document(record, id)
        # Back
        return record


    def update_record(self, id, **kw):
        record = self.records[id]
        version = record[-1].copy()
        for name, value in kw.items():
            datatype = self.get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                value = [ x if isinstance(x, Property) else Property(x)
                          for x in value ]
            elif not isinstance(value, Property):
                value = Property(value)
            version[name] = value
        version['ts'] = Property(datetime.now())
        # Change
        self.set_changed()
        self.catalog.unindex_document(record, id)
        self.added_records.append((id, len(record)))
        record.append(version)
        # Index
        self.catalog.index_document(record, id)


    def del_record(self, id):
        record = self.records[id]
        # Change
        self.set_changed()
        if (id, 0) not in self.added_records:
            self.removed_records.append((id, datetime.now()))
        self.added_records = [
            (x, y) for x, y in self.added_records if x != id ]
        self.catalog.unindex_document(record, id)
        self.records[id] = None


    def get_record_ids(self):
        i = 0
        for record in self.records:
            if record is not None:
                yield i
            i += 1


    def get_n_records(self):
        ids = self.get_record_ids()
        ids = list(ids)
        return len(ids)


    def get_records(self):
        for id in self.get_record_ids():
            yield self.get_record(id)


    def get_value(self, record, name):
        """
        Return the value if name is in record
        else if name is define in the schema
        return [] is name is a multiple, the default value otherwise.
        """
        try:
            return getattr(record, name)
        except AttributeError:
            if self.schema.has_key(name):
                datatype = self.get_datatype(name)
                if getattr(datatype, 'multiple', False):
                    return []
                else:
                    return getattr(datatype, 'default')


    def search(self, query=None, **kw):
        """
        Return list of row numbers returned by executing the query.
        """
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(PhraseQuery(key, value))

                query = AndQuery(*atoms)
            else:
                raise ValueError, "expected a query"

        documents = query.search(self)
        # Sort by weight
        ids = documents.keys()
        ids.sort()

        return [ self.records[x] for x in ids ]

