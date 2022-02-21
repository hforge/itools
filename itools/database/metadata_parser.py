# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2007-2008 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2007-2008, 2010 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
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

# Import from itools
from itools.core import lazy
from itools.datatypes import String, Unicode


###########################################################################
# Parser
###########################################################################
escape_table = (
    ('\r', r'\r'),
    ('\n', r'\n'))


def unescape_data(data, escape_table=escape_table):
    """Unescape the data
    """
    out = []
    for segment in data.split(r"\\"):
        for c, c_escaped in escape_table:
            segment = segment.replace(c_escaped, c)
        out.append(segment)

    return '\\'.join(out)


def escape_data(data, escape_table=escape_table):
    """Escape the data
    """
    data = data.replace("\\", r"\\")
    for c, c_escaped in escape_table:
        data = data.replace(c, c_escaped)
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


# XXX The RFC only allows '-', we allow more because this is used by
# itools.database (metadata). This set matches checkid (itools.handlers)
allowed = frozenset(['-', '_', '.', '@'])
def read_name(line, allowed=allowed):
    """Reads the property name from the line. Returns the name and the
    rest of the line:

        name
        [parameters]value
    """
    # Test first character of name
    c = line[0]
    if not c.isalnum() and c != '-':
        raise SyntaxError('unexpected character (%s)' % c)

    # Test the rest
    idx = 1
    n = len(line)
    while idx < n:
        c = line[idx]
        if c in (';', ':'):
            return line[:idx], line[idx:]
        if c.isalnum() or c in allowed:
            idx += 1
            continue
        raise SyntaxError("unexpected character '%s' (%s)" % (c, ord(c)))

    raise SyntaxError('unexpected end of line (%s)' % line)


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
                raise SyntaxError(error1 % (c, status))

        # param-name begun
        elif status == 2:
            if c.isalnum() or c in ('-', '_'):
                param_name += c
            elif c == '=':
                parameters[param_name] = []
                status = 3
            else:
                raise SyntaxError(error1 % (c, status))

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
                status = 6
            elif c == "\\":
                param_value += c
                status = 41
            else:
                param_value += c

        elif status == 41: # XXX Special case (not for ical)
            param_value += c
            status = 4

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
                raise SyntaxError(error1 % (c, status))
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
                raise SyntaxError(error1 % (c, status))

    if status not in (7, 8):
        raise SyntaxError('unexpected property (%s)' % property)

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
    if type(data) is bytes:
        data = data.decode("utf-8")
    for line in unfold_lines(data):
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
            raise ValueError('parameter "{0}" not defined'.format(name))
        # Decode
        value = parameters[name]
        value = [ decode_param_value(x, datatype) for x in value ]
        # Multiple or single
        if not datatype.multiple:
            if len(value) > 1:
                msg = 'parameter "%s" must be a singleton'
                raise ValueError(msg % name)
            value = value[0]
        # Update
        parameters[name] = value


class MetadataProperty(object):
    """A property has a value, and may have one or more parameters.

    The parameters is a dictionary containing a list of values:

        {param1_name: [param_values], ...}
    """

    def __init__(self, raw_value, datatype=None, **kw):
        self.raw_value = raw_value
        self.datatype = datatype
        self.parameters = kw or None


    @lazy
    def value(self):
        if self.datatype:
            return self.datatype.decode(self.raw_value)
        return self.raw_value

    def clone(self):
        # Copy the value and parameters
        value = deepcopy(self.value)
        parameters = {}
        for p_key, p_value in self.parameters.items():
            c_value = deepcopy(p_value)
            parameters[p_key] = c_value
        return MetadataProperty(value, self.datatype, **parameters)

    def get_parameter(self, name, default=None):
        if self.parameters is None:
            return default
        return self.parameters.get(name, default)

    def set_parameter(self, name, value):
        if self.parameters is None:
            self.parameters = {}
        self.parameters[name] = value

    def __eq__(self, other):
        if type(other) is not MetadataProperty:
            return False
        if self.value != other.value:
            return False
        return self.parameters == other.parameters

    def __ne__(self, other):
        return not self.__eq__(other)


params_escape_table = (
    ('"', r'\"'),
    ('\r', r'\r'),
    ('\n', r'\n'))


def encode_param_value(p_name, p_value, p_datatype):
    p_value = p_datatype.encode(p_value)

    # Special case (not used by ical)
    if getattr(p_datatype, 'escape', False):
        p_value = escape_data(p_value, params_escape_table)
        return '"%s"' % p_value

    # Standard case (ical behavior)
    if '"' in p_value or '\n' in p_value:
        error = 'the "%s" parameter contains a double quote'
        raise ValueError(error % p_name)
    if ';' in p_value or ':' in p_value or ',' in p_value:
        return '"%s"' % p_value
    return p_value


def decode_param_value(p_value, p_datatype):
    # Special case (not used by ical)
    if getattr(p_datatype, 'escape', False):
        p_value = unescape_data(p_value, params_escape_table)

    return p_datatype.decode(p_value)


def _property_to_str(name, property, datatype, p_schema, encoding='utf-8'):
    """This method serializes the given property to a byte string:

      name[;parameters]=value

    The given datatype is used to serialize the property value.  The given
    'p_schema' describes the parameters.
    """
    # Parameters
    if property.parameters:
        p_names = list(property.parameters.keys())
        p_names = sorted(p_names)
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
        raise ValueError('property "{0}" is not str but {1}'.format(
            name, type(value)))
    value = escape_data(value)
    if datatype.encrypted:
        value = datatype.encrypt(value)

    # Ok
    property = '%s%s:%s\n' % (name, parameters, value)
    return fold_line(property)


def property_to_str(name, property, datatype, p_schema, encoding='utf-8'):
    try:
        return _property_to_str(name, property, datatype, p_schema, encoding)
    except Exception:
        err = 'failed to serialize "%s" property, probably a bad value'
        raise ValueError(err % name)
