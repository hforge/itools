# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2007-2008 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2008, 2010 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008-2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Alexis Huet <alexis@itaapy.com>
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
from copy import deepcopy
from datetime import datetime

# Import from itools
from itools.datatypes import DateTime, String, Unicode
from itools.handlers import File
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

def get_tokens(property):
    parameters = {}
    value = ''
    status = 0

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
            if c.isalnum() or c in ('-', '_'):
                param_name += c
            elif c == '=':
                parameters[param_name] = []
                status = 3
            else:
                raise SyntaxError, error1 % (c, status)

        # param-name ended, param-value beginning
        elif status == 3:
            if c == '"':
                param_value = ''
                status = 4
            elif c == ':':
                parameters[param_name].append('')
                status = 7
            elif c == ';':
                parameters[param_name].append('')
                status = 1
            elif c == ',':
                parameters[param_name].append('')
            else:
                param_value = c
                status = 5

        # param-value quoted begun (just after '"')
        elif status == 4:
            if c == '"':
                # XXX We don't allow the empty value (""), is that right?
                if not param_value:
                    raise SyntaxError, 'unexpected empty string ("")'
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
    return getattr(datatype, 'multilingual', False)


def is_multiple(datatype):
    return getattr(datatype, 'multiple', False)


def deserialize_parameters(parameters, schema, default=String(multiple=True)):
    for name in parameters:
        datatype = schema.get(name, default)
        if datatype is None:
            raise ValueError, 'parameter "{0}" not defined'.format(name)
        # Decode
        value = parameters[name]
        value = [ datatype.decode(x) for x in value ]
        # Multiple or single
        if not datatype.multiple:
            if len(value) > 1:
                msg = 'parameter "%s" must be a singleton'
                raise ValueError, msg % name
            value = value[0]
        # Update
        parameters[name] = value



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
            u' already used.').format(field=self.name, value=self.value)


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
        self.parameters = kw or None


    def clone(self):
        # Copy the value and parameters
        value = deepcopy(self.value)
        parameters = {}
        for p_key, p_value in self.parameters.iteritems():
            c_value = deepcopy(p_value)
            parameters[p_key] = c_value

        return Property(value, **parameters)


    def get_parameter(self, name, default=None):
        if self.parameters is None:
            return default
        return self.parameters.get(name, default)


    def set_parameter(self, name, value):
        if self.parameters is None:
            self.parameters = {}
        self.parameters[name] = value


    def __eq__(self, other):
        if type(other) is not Property:
            return False
        if self.value != other.value:
            return False
        return self.parameters == other.parameters


    def __ne__(self, other):
        return not self.__eq__(other)



def encode_param_value(p_name, p_value, p_datatype):
    p_value = p_datatype.encode(p_value)
    if '"' in p_value:
        error = 'the "%s" parameter contains a double quote'
        raise ValueError, error % p_name
    if ';' in p_value or ':' in p_value or ',' in p_value:
        return '"%s"' % p_value
    return p_value



def property_to_str(name, property, datatype, p_schema, encoding='utf-8'):
    """This method serializes the given property to a byte string:

      name[;parameters]=value

    The given datatype is used to serialize the property value.  The given
    'p_schema' describes the parameters.
    """
    # Parameters
    if property.parameters:
        p_names = property.parameters.keys()
        p_names.sort()
    else:
        p_names = []

    parameters = []
    for p_name in p_names:
        p_value = property.parameters[p_name]
        if p_value is None:
            continue
        # Find out the datatype for the parameter
        p_datatype = p_schema.get(p_name)
        if not p_datatype:
            p_datatype = String(multiple=True)
        # Serialize the parameter
        # FIXME Use the encoding
        if is_multiple(p_datatype):
            p_value = [
                encode_param_value(p_name, x, p_datatype) for x in p_value ]
            p_value = ','.join(p_value)
        else:
            p_value = encode_param_value(p_name, p_value, p_datatype)
        parameters.append(';%s=%s' % (p_name, p_value))
    parameters = ''.join(parameters)

    # Value
    if isinstance(datatype, Unicode):
        value = datatype.encode(property.value, encoding=encoding)
    else:
        value = datatype.encode(property.value)
    if type(value) is not str:
        raise ValueError, 'property "{0}" is not str but {1}'.format(
                name, type(value))
    value = escape_data(value)

    # Ok
    property = '%s%s:%s\n' % (name, parameters, value)
    return fold_line(property)



class Record(dict):

    __slots__ = ['id', 'record_properties']


    def __init__(self, id, record_properties):
        self.id = id
        self.record_properties  = record_properties


    def __getattr__(self, name):
        if name == '__number__':
            return self.id
        if name not in self:
            raise AttributeError, "'%s' object has no attribute '%s'" % (
                self.__class__.__name__, name)

        property = self[name]
        if type(property) is list:
            return [ x.value for x in property ]
        return property.value


    def get_property(self, name):
        return self.get(name)


    # For indexing purposes
    def get_value(self, name):
        property = self.get(name)
        if property is None:
            return None

        if type(property) is list:
            return [ x.value for x in property ]
        return property.value



class Table(File):

    record_class = Record

    #######################################################################
    # Hash with field names and its types
    # Example: {'firstname': Unicode, 'lastname': Unicode, 'age': Integer}
    #######################################################################
    schema = {}
    record_properties = {}
    record_parameters = {
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
        if name in self.record_properties:
            return self.record_properties[name]
        # FIXME Probably we should raise an exception here
        return String(multiple=True)


    def properties_to_dict(self, properties, record, first=False):
        """Add the given "properties" as Property objects or Property objects
        list to the given dictionnary "record".
        """
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
                if type(value) is not list:
                    value = [ value ]
                record.setdefault(name, [])
                for p in value:
                    language = p.parameters['language']
                    record[name] = [
                        x for x in record[name]
                        if x.parameters['language'] != language ]
                    record[name].append(p)
            elif datatype.multiple:
                if type(value) is list:
                    record[name] = [ to_property(x) for x in value ]
                else:
                    record[name] = [to_property(value)]
            else:
                record[name] = to_property(value)


    #######################################################################
    # Handlers
    #######################################################################
    def reset(self):
        self.properties = None
        self.records = []
        self.changed_properties = False


    def new(self):
        # Add the properties record
        properties = self.record_class(-1, self.record_properties)
        properties['ts'] = Property(datetime.now())
        self.properties = properties


    def _load_state_from_file(self, file):
        # Load the records
        records = self.records
        record_properties = self.record_properties

        n = 0
        for name, value, parameters in parse_table(file.read()):
            if name == 'id':
                uid, seq = value.split('/')
                uid = int(uid)
                # Build the new record
                if seq == 'DELETED':
                    record = None
                else:
                    record = self.record_class(uid, record_properties)
                # Table properties, or new record, or updated record
                if uid == -1:
                    get_datatype = self.get_datatype
                    self.properties = record
                elif uid >= n:
                    get_datatype = self.get_record_datatype
                    records.extend([None] * (uid - n))
                    records.append(record)
                    n = uid + 1
                else:
                    get_datatype = self.get_record_datatype
                    records[uid] = record
                # Continue
                continue

            # Skip deleted records
            if record is None:
                continue

            # Deserialize the parameters
            deserialize_parameters(parameters, self.record_parameters)

            # Timestamp (ts), Schema, or Something else
            datatype = get_datatype(name)
            value = datatype.decode(value)
            property = Property(value, **parameters)
            if is_multilingual(datatype) or is_multiple(datatype):
                record.setdefault(name, []).append(property)
            elif name in record:
                msg = "record %s: property '%s' can occur only once"
                raise ValueError, msg % (uid, name)
            else:
                record[name] = property


    def _record_to_str(self, id, record):
        lines = ['id:%d/0\n' % id]
        names = record.keys()
        names.sort()
        # Table or record schema
        if id == -1:
            get_datatype = self.get_datatype
        else:
            get_datatype = self.get_record_datatype

        # Loop
        p_schema = self.record_parameters
        for name in names:
            datatype = get_datatype(name)
            if is_multilingual(datatype) or is_multiple(datatype):
                properties = record[name]
            else:
                properties = [record[name]]
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
        # Properties record
        if self.properties is not None:
            record = self._record_to_str(-1, self.properties)
            lines.append(record)
        # Common record
        id = 0
        for record in self.records:
            if record is not None:
                record = self._record_to_str(id, record)
                lines.append(record)
            # Next
            id += 1

        return ''.join(lines)


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
                if self.search(name, kw[name]):
                    raise UniqueError(name, kw[name])
        # Make new record
        id = len(self.records)
        record = self.record_class(id, self.record_properties)
        self.properties_to_dict(kw, record)
        record['ts'] = Property(datetime.now())
        # Change
        self.set_changed()
        self.records.append(record)
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
                search = self.search(name, kw[name])
                if search and (search[0] != self.records[id]):
                    raise UniqueError(name, kw[name])
        # Update record
        self.set_changed()
        self.properties_to_dict(kw, record)
        record['ts'] = Property(datetime.now())


    def update_properties(self, **kw):
        record = self.properties
        if record is None:
            # if the record doesn't exist
            # we create it, it's useful during an update
            record = self.record_class(-1, self.record_properties)
            self.properties = record

        self.properties_to_dict(kw, record, first=True)
        record['ts'] = Property(datetime.now())
        # Change
        self.set_changed()
        self.changed_properties = True


    def del_record(self, id):
        record = self.records[id]
        if record is None:
            msg = 'cannot delete record "%s" because it was deleted before'
            raise LookupError, msg % id
        # Change
        self.set_changed()
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
        return ( x for x in self.records if x )


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
                languages = [ x.parameters['language'] for x in property
                              if not datatype.is_empty(x.value) ]
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
                default = datatype.get_default()
                # FIXME raise a TypeError instead
                if type(default) is not list:
                    return []
                return default
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
            if name in self.record_properties:
                datatype = self.get_datatype(name)
                if is_multilingual(datatype) or is_multiple(datatype):
                    return []
                else:
                    return getattr(datatype, 'default')


    def search(self, key, value):
        get = self.get_record_value
        return [ x for x in self.records if x and get(x, key) == value ]


    def update_from_csv(self, data, columns, skip_header=False):
        """Update the table by adding record from data
        The input parameters are :

        - 'data': the bytes string representation of a CSV.
        - 'columns': the CSV columns used for the mapping between the CSV
          columns and the table schema.
        """
        record_properties = self.record_properties
        for line in parse(data, columns, record_properties,
                skip_header=skip_header):
            record = {}
            for index, key in enumerate(columns):
                if key in record_properties:
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
