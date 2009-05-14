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
from itools.core import merge_dicts
from itools.datatypes import DateTime, String, Integer, Unicode
from itools.handlers import File
from itools import vfs
from itools.xapian import make_catalog
from itools.xapian import AndQuery, PhraseQuery, CatalogAware
from csv_ import CSVFile
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
        if next and (next[0] == ' ' or next[0] == '\t'):
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
    # Test first character of name
    c = line[0]
    if not c.isalnum() and c != '-':
        raise SyntaxError, 'unexpected character (%s)' % c

    # Test the rest
    idx = 1
    n = len(line)
    while idx < n:
        c = line[idx]
        if c in (';', ':'):
            return line[:idx], line[idx:]
        if c.isalnum() or c in ('-', '_'):
            idx += 1
            continue
        raise SyntaxError, "unexpected character '%s' (%s)" % (c, ord(c))

    raise SyntaxError, 'unexpected end of line (%s)' % line


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

error1 = 'unexpected character (%s) at status %s'
error2 = 'unexpected repeated character (%s) at status %s'

def get_tokens(property):
    parameters = {}
    value = ''
    status, last = 0, ''

    # Init status
    c, property = property[0], property[1:]
    if c == ';':
        status = 1
    elif c == ':':
        status = 7

    for c in property:
        # value begun
        if status == 8:
            value += c

        # parameter begun (just after ';')
        elif status == 1:
            if c.isalnum() or c in ('-'):
                param_name, status = c, 2
            else:
                raise SyntaxError, error1 % (c, status)

        # param-name begun
        elif status == 2:
            if c.isalnum() or c in ('-'):
                param_name += c
            elif c == '=':
                parameters[param_name] = []
                status = 3
            else:
                raise SyntaxError, error1 % (c, status)

        # param-name ended, param-value beginning
        elif status == 3:
            if c == '"':
                param_value = c
                status = 4
            elif c in (';', ':', ',') :
                raise SyntaxError, error1 % (c, status)
            else:
                param_value = c
                status = 5

        # param-value quoted begun (just after '"')
        elif status == 4:
            if c == '"':
                if last == '"':
                    raise SyntaxError, error2 % (c, status)
                last = '"'
                param_value += c
                status = 6
            else:
                param_value += c

        # param-value NOT quoted begun
        elif status == 5:
            if c == ':':
                parameters[param_name].append(param_value)
                status = 7
            elif c == ';':
                parameters[param_name].append(param_value)
                status = 1
            elif c == ',':
                parameters[param_name].append(param_value)
                status = 3
            elif c == '"':
                raise SyntaxError, error1 % (c, status)
            else:
                param_value += c

        # value to begin (just after ':')
        elif status == 7:
            value, status = c, 8

        # param-value ended (just after '"' for quoted ones)
        elif status == 6:
            parameters[param_name].append(param_value)
            if c == ':':
                status = 7
            elif c == ';':
                status = 1
            elif c == ',':
                status = 3
            else:
                raise SyntaxError, error1 % (c, status)

    if status not in (7, 8):
        raise SyntaxError, 'unexpected property (%s)' % property

    # Unescape special characters (TODO Check the spec)
    value = unescape_data(value)
    return value, parameters



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
        value, parameters = get_tokens(line)
        yield name, value, parameters



###########################################################################
# Helper functions
###########################################################################
def is_multilingual(datatype):
    return issubclass(datatype, Unicode) and datatype.multiple



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
        return (
            u'the "{field}" field must be unique, the "{value}" value is '
            u' already used.')


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


def property_to_str(name, property, datatype, p_schema, encoding='utf-8'):
    """This method serializes the given property to a byte string:

      name[;parameters]=value

    The given datatype is used to serialize the property value.  The given
    'p_schema' describes the parameters.
    """
    # Parameters
    parameters = []
    p_names = property.parameters.keys()
    p_names.sort()
    for p_name in p_names:
        p_value = property.parameters[p_name]
        # Find out the datatype for the parameter
        p_datatype = p_schema.get(p_name)
        if not p_datatype:
            p_datatype = String(multiple=True)
        # Serialize the parameter
        # FIXME Use the encoding
        if getattr(p_datatype, 'multiple', False):
            p_value = [ p_datatype.encode(x) for x in p_value ]
            p_value = ','.join(p_value)
        else:
            p_value = p_datatype.encode(p_value)
        parameters.append(';%s=%s' % (p_name, p_value))
    parameters = ''.join(parameters)

    # Value
    if isinstance(datatype, Unicode):
        value = datatype.encode(property.value, encoding=encoding)
    else:
        value = datatype.encode(property.value)
    value = escape_data(value)

    # Ok
    property = '%s%s:%s\n' % (name, parameters, value)
    return fold_line(property)



class Record(list, CatalogAware):

    __slots__ = ['id', 'record_schema']


    def __init__(self, id, record_schema):
        self.id = id
        self.record_schema  = record_schema


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


    def get_catalog_values(self):
        values = {'__id__': self.id}
        for name in self.record_schema.iterkeys():
            values[name] = self.get_value(name)
        return values



class Table(File):

    record_class = Record
    incremental_save = True

    #######################################################################
    # Hash with field names and its types
    # Example: {'firstname': Unicode, 'lastname': Unicode, 'age': Integer}
    # To index some fields the schema should be declared as:
    # record_schema = {'firstname': Unicode, 'lastname': Unicode,
    #                  'age': Integer(is_indexed=True)}
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
        return String(multiple=True)


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

            # Transform values to properties
            if is_multilingual(datatype):
                language = value.parameters['language']
                version.setdefault(name, [])
                version[name] = [
                    x for x in version[name]
                    if x.parameters['language'] != language ]
                version[name].append(value)
            elif datatype.multiple:
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
    clone_exclude = File.clone_exclude | frozenset(['catalog'])


    def reset(self):
        self.properties = None
        self.records = []
        self.added_properties = []
        self.added_records = []
        self.removed_records = []
        # The catalog (for index and search)
        fields = merge_dicts(self.record_schema,
                             __id__=Integer(is_key_field=True, is_stored=True,
                                            is_indexed=True))
        self.catalog = make_catalog(None, fields)


    def new(self):
        # Add the properties record
        properties = self.record_class(-1, self.record_schema)
        properties.append({'ts': Property(datetime.now())})
        self.properties = properties


    def _load_state_from_file(self, file):
        # Load the records
        records = self.records
        properties = self.properties
        record_schema = self.record_schema

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
                        properties = self.record_class(uid, record_schema)
                        self.properties = properties
                    record = properties
                elif uid >= n:
                    # New record
                    records.extend([None] * (uid - n))
                    record = self.record_class(uid, record_schema)
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
                if not param_type.multiple:
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
                self.catalog.index_document(record)


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
        p_schema = self.parameters_schema
        for name in names:
            datatype = get_datatype(name)
            if getattr(datatype, 'multiple', False) is True:
                properties = version[name]
            else:
                properties = [version[name]]
            for property in properties:
                if property.value is None:
                    continue
                property = property_to_str(name, property, datatype, p_schema)
                lines.append(property)

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
        if self.incremental_save is False:
            File.save_state(self)
            self.incremental_save = True
            return

        # Incremental Save
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
    # API / Public
    #######################################################################
    def get_record(self, id):
        try:
            return self.records[id]
        except IndexError:
            return None


    def add_record(self, kw):
        # Check for duplicate
        for name in kw:
            datatype = self.get_record_datatype(name)
            if getattr(datatype, 'unique', False) is True:
                if len(self.search(PhraseQuery(name, kw[name]))) > 0:
                    raise UniqueError(name, kw[name])
        # Add version to record
        id = len(self.records)
        record = self.record_class(id, self.record_schema)
        version = self.properties_to_dict(kw)
        version['ts'] = Property(datetime.now())
        record.append(version)
        # Change
        self.set_changed()
        self.added_records.append((id, 0))
        self.records.append(record)
        self.catalog.index_document(record)
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
        self.catalog.unindex_document(record.id)
        self.added_records.append((id, len(record)))
        record.append(version)
        # Index
        self.catalog.index_document(record)


    def update_properties(self, **kw):
        record = self.properties
        if record is None:
            # if the record doesn't exist
            # we create it, it's useful during an update
            record = self.record_class(-1, self.record_schema)
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
        self.catalog.unindex_document(record.id)
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
        if is_multilingual(datatype):
            # Default
            if property is None:
                return datatype.get_default()
            # Language negotiation ('select_language' is a built-in)
            if language is None:
                languages = [ x.parameters['language'] for x in property ]
                language = select_language(languages)
                if language is None and languages:
                    # Pick up one at random (FIXME)
                    language = languages[0]
            # Miss: default
            if language is None:
                return datatype.get_default()
            # Hit
            for x in property:
                if x.parameters['language'] == language:
                    return x.value
            # Default
            return datatype.get_default()

        # Multiple values
        if datatype.multiple:
            # Default
            if property is None:
                # FIXME Probably we should check whether the datatype defines
                # a default value.
                return []
            # Hit
            return [ x.value for x in property ]

        # Simple properties
        if property is None:
            return datatype.get_default()
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
        result = self.catalog.search(query, **kw)
        ids = [ doc.__id__ for doc in result.get_documents(sort_by='__id__') ]
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


    def to_csv(self, columns, separator=None, language=None):
        """Export the table to CSV handler.
        As table columns are unordered, the order comes from the "columns"
        parameter.
        separator: join multiple values with this string
        language: affects multilingual columns
        """
        csv = CSVFile()

        for record in self.get_records():
            line = []
            for column in columns:
                datatype = self.get_record_datatype(column)
                value = self.get_record_value(record, column,
                                              language=language)
                if not is_multilingual(datatype) and datatype.multiple:
                    if separator is not None:
                        values = [datatype.encode(v) for v in value]
                        data = separator.join(values)
                    else:
                        # TODO represent multiple values
                        message = ("multiple values are not supported, "
                                   "use a separator")
                        raise NotImplementedError, message
                else:
                    data = datatype.encode(value)
                line.append(data)
            csv.add_row(line)

        return csv
