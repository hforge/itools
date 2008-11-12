# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.datatypes import DateTime, String, Integer, Unicode, is_datatype
from itools.handlers import File
from itools import vfs
from itools.xapian import AndQuery, PhraseQuery, get_field
from memory import MemoryCatalog
from parser import parse


###########################################################################
# Parser
###########################################################################
def unescape_data(data):
    """Unescape the data
    """
    data = [ x.replace("\\r", "\r").replace("\\n", "\n")
              for x in data.split('\\\\') ]
    return '\\'.join(data)



def escape_data(data):
    """Escape the data
    """
    data = data.replace("\\", "\\\\")
    data = data.replace("\r", "\\r").replace("\n", "\\n")
    return data



def unfold_lines(data):
    """Unfold the folded lines.
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



def fold_line(data):
    """Fold the unfolded line over 75 characters.
    """
    if len(data) <= 75:
        return data

    i = 1
    lines = data.split(' ')
    res = lines[0]
    size = len(res)
    while i < len(lines):
        # Still less than 75c
        if size+len(lines[i]) <= 75:
            res = res + ' ' + lines[i]
            size = size + 1 + len(lines[i])
            i = i + 1
        # More than 75c, insert new line
        else:
            res = res + '\n  ' + lines[i]
            size = len(lines[i])
            i = i + 1
    return res



def read_name(line):
    """Reads the property name from the line. Returns the name and the
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
TPARAM, TVALUE = 0, 1
token_name = ['name', 'parameter', 'value']


def get_tokens(property):
    status, lexeme, last = 0, '', ''

    # Init status
    c, property = property[0], property[1:]
    if c == ';':
        status = 1
    elif c == ':':
        status = 7

    error1 = 'unexpected character (%s) at status %s'
    error2 = 'unexpected repeated character (%s) at status %s'

    for c in property:
        # parameter begun (just after ';')
        if status == 1:
            if c.isalnum() or c in ('-'):
                lexeme, status = c, 2
            else:
                raise SyntaxError, error1 % (c, status)

        # param-name begun
        elif status == 2:
            if c.isalnum() or c in ('-'):
                lexeme += c
            elif c == '=':
                lexeme += c
                status = 3
            else:
                raise SyntaxError, error1 % (c, status)

        # param-name ended, param-value beginning
        elif status == 3:
            if c == '"':
                lexeme += c
                status = 4
            elif c in (';', ':', ',') :
                raise SyntaxError, error1 % (c, status)
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
            if c in (':', ';', ',') :
                status = 6
            elif c=='"':
                raise SyntaxError, error1 % (c, status)
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
                    raise SyntaxError, error2 % (c, status)
                last = '"'
            else:
                raise SyntaxError, error1 % (c, status)

    if status not in (7, 8):
        raise SyntaxError, 'unexpected property (%s)' % property

    yield TVALUE, lexeme



def parse_table(data):
    """This is the public interface of the module "itools.ical.parser", a
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
                value = unescape_data(lexeme)
            else:
                raise SyntaxError, 'unexpected %s' % token_name[token]
        yield name, value, parameters


###########################################################################
# UniqueError
###########################################################################
class UniqueError(ValueError):
    """Raised when setting a value already used to a unique property.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value


    def __str__(self):
        return (u'Error: Field "$field" must be unique, '
                u'value "$value" is already used.')


###########################################################################
# File Handler
###########################################################################
class Property(object):
    """A property has a value, and may have one or more parameters.

    The parameters is a dictionary containing a list of values:

        {param1_name: [param_values], ...}
    """

    __slots__ = ['value', 'parameters']

    def __init__(self, value, **kw):
        self.value = value
        self.parameters = kw



class Record(list):

    __slots__ = ['id']


    def __init__(self, id):
        self.id = id


    def __getattr__(self, name):
        if name == '__number__':
            return self.id
        version = self[-1]
        if name not in version:
            raise AttributeError, "'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name)

        property = version[name]
        if type(property) is list:
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
        if type(property) is list:
            return [ x.value for x in property ]
        return property.value



class Table(File):

    record_class = Record

    #######################################################################
    # Hash with field names and its types
    # Example: {'firstname': Unicode, 'lastname': Unicode, 'age': Integer}
    # To index some fields the schema should be declared as:
    # record_schema = {'firstname': Unicode, 'lastname': Unicode,
    #                  'age': Integer(index='<analyser>')}
    # where <analyser> is an itools.xapian analyser or derivate: keyword,
    # book, text, path.
    #######################################################################
    schema = {}
    record_schema = {}
    parameters_schema = {
        'language': String(multiple=False)}


    def get_datatype(self, name):
        # Table schema
        if name == 'ts':
            return DateTime(multiple=False)
        if name in self.schema:
            return self.schema[name]
        return String(multiple=True)


    def get_record_datatype(self, name):
        # Record schema
        if name == 'ts':
            return DateTime(multiple=False)
        if name in self.record_schema:
            return self.record_schema[name]
        # FIXME Probably we should raise an exception here
        return String(multiple=True)


    def get_parameter_datatype(self, name):
        # Record schema
        schema = self.parameters_schema
        if name in schema:
            return schema[name]
        return String


    def properties_to_dict(self, properties, version=None, first=False):
        """Add the given "properties" as Property objects or Property objects
        list to the given dictionnary "version".
        """
        if version is None:
            version = {}

        # The variable 'first' defines whether we are talking about the
        # table properties (True) or a about records (False).
        if first is True:
            get_datatype = self.get_datatype
        else:
            get_datatype = self.get_record_datatype

        # Fix the type
        to_property = lambda x: x if isinstance(x, Property) else Property(x)
        for name in properties:
            value = properties[name]
            datatype = get_datatype(name)
            is_multiple = getattr(datatype, 'multiple', False)

            # Transform values to properties
            if is_datatype(datatype, Unicode):
                language = value.parameters['language']
                version.setdefault(name, [])
                version[name] = [
                    x for x in version[name]
                    if x.parameters['language'] != language ]
                version[name].append(value)
            elif is_multiple:
                if type(value) is list:
                    version[name] = [ to_property(x) for x in value ]
                else:
                    version[name] = [to_property(value)]
            else:
                version[name] = to_property(value)
        return version


    #######################################################################
    # Handlers
    #######################################################################
    def reset(self):
        self.properties = None
        self.records = []
        self.added_properties = []
        self.added_records = []
        self.removed_records = []
        # The catalog (for index and search)
        self.catalog = MemoryCatalog()
        for name, datatype in self.record_schema.items():
            index = getattr(datatype, 'index', None)
            if index is not None:
                field = get_field(index)
                self.catalog.add_index(name, field)


    def new(self):
        # Add the properties record
        properties = self.record_class(-1)
        properties.append({'ts': Property(datetime.now())})
        self.properties = properties


    def _load_state_from_file(self, file):
        # Load the records
        records = self.records
        properties = self.properties
        n = 0
        version = None
        for name, value, parameters in parse_table(file.read()):
            if name == 'id':
                version = {}
                # Identifier and Sequence (id)
                uid, seq = value.split('/')
                # Record
                uid = int(uid)
                if uid == -1:
                    # Tale properties
                    if properties is None:
                        properties = self.record_class(uid)
                        self.properties = properties
                    record = properties
                elif uid >= n:
                    # New record
                    records.extend([None] * (uid - n))
                    record = self.record_class(uid)
                    records.append(record)
                    n = uid + 1
                else:
                    # Get the record
                    record = records[uid]
                # Version
                if seq == 'DELETED':
                    # Deleted
                    if uid == -1:
                        properties = None
                    else:
                        records[uid] = None
                        record = None
                else:
                    seq = int(seq)
                    if seq > len(record):
                        msg = 'unexpected sequence "%s" for record "%s"'
                        raise ValueError, msg % (seq, uid)
                    record.append(version)
                # Table or record schema
                if uid == -1:
                    get_datatype = self.get_datatype
                else:
                    get_datatype = self.get_record_datatype
                continue

            # Deserialize the parameters
            for param_name in parameters.keys():
                param_value = parameters[param_name]
                param_type = self.get_parameter_datatype(param_name)
                # Decode
                param_value = [ param_type.decode(x) for x in param_value ]
                # Multiple or single
                is_multiple = getattr(param_type, 'multiple', True)
                if not is_multiple:
                    if len(param_value) > 1:
                        msg = 'parameter "%s" must be a singleton'
                        raise ValueError, msg % param_name
                    param_value = param_value[0]
                # Update
                parameters[param_name] = param_value

            # Timestamp (ts), Schema, or Something else
            datatype = get_datatype(name)
            value = datatype.decode(value)
            property = Property(value, **parameters)
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
        # Table or record schema
        if id == -1:
            get_datatype = self.get_datatype
        else:
            get_datatype = self.get_record_datatype

        # Loop
        for name in names:
            datatype = get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                properties = version[name]
            else:
                properties = [version[name]]
            for property in properties:
                if property.value is None:
                    continue
                lines.append(name)
                # Parameters
                pnames = property.parameters.keys()
                pnames.sort()
                for pname in pnames:
                    pvalues = property.parameters[pname]
                    pdatatype = self.get_parameter_datatype(pname)
                    is_multiple = getattr(pdatatype, 'multiple', True)
                    if is_multiple:
                        pvalues = [ pdatatype.encode(x) for x in pvalues ]
                        pvalues = ','.join(pvalues)
                    else:
                        pvalues = pdatatype.encode(pvalues)
                    lines.append(';%s=%s' % (pname, pvalues))
                # Value
                value = datatype.encode(property.value)
                if isinstance(value, Integer):
                    value = str(value)
                # Escape the value
                value = escape_data(value)
                lines.append(':%s\n' % fold_line(value))

        # Ok
        lines.append('\n')
        return ''.join(lines)


    def to_str(self):
        lines = []
        id = 0
        # Properties record
        if self.properties is not None:
            seq = 0
            for version in self.properties:
                version = self._version_to_str(-1, seq, version)
                lines.append(version)
                seq += 1
        # Common record
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
        file = self.safe_open(self.uri, 'a')
        try:
            # Added properties records
            for seq in self.added_properties:
                version = self.properties[seq]
                version = self._version_to_str(-1, seq, version)
                file.write(version)
            self.added_properties = []
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
        finally:
            file.close()

        # Update the timestamp
        self.timestamp = vfs.get_mtime(self.uri)
        self.dirty = None


    def save_state_to(self, uri):
        # TODO: this is a hack, for 0.50 this case should be covered by the
        # handler's protocol
        File.save_state_to(self, uri)
        if uri == self.uri:
            self.added_records = []
            self.removed_records = []


    #######################################################################
    # API / Private
    #######################################################################
    def get_analyser(self, name):
        datatype = self.get_record_datatype(name)
        return get_field(datatype.index)


    def get_index(self, name):
        if name not in self.record_schema:
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
        # Check for duplicate
        for name in kw:
            datatype = self.get_record_datatype(name)
            if getattr(datatype, 'unique', False) is True:
                search = self.search(PhraseQuery(name, kw[name]))
                if len(self.search(PhraseQuery(name, kw[name]))) > 0:
                    raise UniqueError(name, kw[name])
        # Add version to record
        id = len(self.records)
        record = self.record_class(id)
        version = self.properties_to_dict(kw)
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
        if record is None:
            msg = 'cannot modify record "%s" because it has been deleted'
            raise LookupError, msg % id
        # Check for duplicate
        for name in kw:
            datatype = self.get_record_datatype(name)
            if getattr(datatype, 'unique', False) is True:
                search = self.search(PhraseQuery(name, kw[name]))
                if search and (search[0] != self.records[id]):
                    raise UniqueError(name, kw[name])
        # Version of record
        version = record[-1].copy()
        version = self.properties_to_dict(kw, version)
        version['ts'] = Property(datetime.now())
        # Change
        self.set_changed()
        self.catalog.unindex_document(record, id)
        self.added_records.append((id, len(record)))
        record.append(version)
        # Index
        self.catalog.index_document(record, id)


    def update_properties(self, **kw):
        record = self.properties
        if record is None:
            # if the record doesn't exist
            # we create it, it's useful during an update
            record = self.record_class(-1)
            version = None
            self.properties = record
        else:
            # Version of record
            version = record[-1].copy()
        version = self.properties_to_dict(kw, version, first=True)
        version['ts'] = Property(datetime.now())
        # Change
        self.set_changed()
        self.added_properties.append(len(record))
        record.append(version)


    def del_record(self, id):
        record = self.records[id]
        if record is None:
            msg = 'cannot delete record "%s" because it was deleted before'
            raise LookupError, msg % id
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


    def get_record_value(self, record, name, language=None):
        """This is the preferred method for accessing record values.  It
        returns the value for the given record object and name.

        If the record has not a value with the given name, returns the
        default value.
        """
        # The 'id' is a particular case
        if name == 'id':
            return record.id

        # Get the property
        property = record.get_property(name)
        datatype = self.get_record_datatype(name)

        # Multilingual properties
        if is_datatype(datatype, Unicode):
            # Default
            if property is None:
                return datatype.default
            # Language negotiation ('select_language' must be available)
            if language is None:
                languages = [ x.parameters['language'] for x in property ]
                language = select_language(languages)
            # Miss: default
            if language is None:
                # XXX Should send any value?
                return datatype.default
            # Hit
            for x in property:
                if x.parameters['language'] == language:
                    return x.value
            # Default
            return datatype.default

        # Multiple values
        is_multiple = getattr(datatype, 'multiple', False)
        if is_multiple:
            # Default
            if property is None:
                # FIXME Probably we should check whether the datatype defines
                # a default value.
                return []
            # Hit
            return [ x.value for x in property ]

        # Simple properties
        if property is None:
            return datatype.default
        return property.value


    def get_property(self, name):
        record = self.properties
        return record.get_value(name)


    def get_property_value(self, name):
        """Return the value if name is in record
        else if name is define in the schema
        return [] is name is a multiple, the default value otherwise.
        """
        record = self.properties
        if name == 'id':
            return record.id
        try:
            return getattr(record, name)
        except AttributeError:
            if name in self.record_schema:
                datatype = self.get_datatype(name)
                if getattr(datatype, 'multiple', False) is True:
                    return []
                else:
                    return getattr(datatype, 'default')


    def search(self, query=None, **kw):
        """Return list of row numbers returned by executing the query.
        """
        if query is None:
            if kw:
                atoms = []
                for key, value in kw.items():
                    atoms.append(PhraseQuery(key, value))

                query = AndQuery(*atoms)
            else:
                return self.get_records()

        documents = query.search(self)
        # Sort by weight
        ids = documents.keys()
        ids.sort()

        return [ self.records[x] for x in ids ]


    def update_from_csv(self, data, columns):
        """Update the table by adding record from data
        The input parameters are :

        - 'data': the bytes string representation of a CSV.
        - 'columns': the CSV columns used for the mapping between the CSV
          columns and the table schema.
        """
        record_schema = self.record_schema
        for line in parse(data, columns, record_schema):
            record = {}
            for index, key in enumerate(columns):
                if key in record_schema:
                    record[key] = line[index]
            self.add_record(record)

