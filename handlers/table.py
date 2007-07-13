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

# Import from itools
from itools.datatypes import DateTime
from itools.catalog import MemoryCatalog
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
        if c.isalnum() or c == '-':
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
class Table(File):
    
    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'records', 'catalog']


    schema = {}


    def new(self):
        self.records = []
        self.catalog = MemoryCatalog()


    def _load_state_from_file(self, file):
        self.new()

        records = self.records
        n = 0
        version = None

        data = file.read()
        for name, value, parameters in parse_table(data):
            # Identifier and Sequence (id)
            if name == 'id':
                uid, seq = value.split('/')
                # Record
                uid = int(uid)
                if uid >= n:
                    # New record
                    records.extend([None] * (uid - n))
                    record = []
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
                    version = {}
                    record.append(version)
            # Timestamp (ts)
            elif name == 'ts':
                version['ts'] = DateTime.decode(value)
            # Something else
            elif name in self.schema:
                datatype = self.schema[name]
                version[name] = datatype.decode(value)
            # Error
            else:
                msg = 'unexepect field "%s" for record "%s/%s"'
                raise ValueError, msg % (name, uid, seq)


    def to_str(self):
        lines = []

        uid = 0
        for record in self.records:
            if record is not None:
                seq = 0
                for version in record:
                    lines.append('id:%d/%d' % (uid, seq))
                    for name, value in version.items():
                        if name == 'ts':
                            datatype = DateTime
                        elif name in self.schema:
                            datatype = self.schema[name]
                        value = datatype.encode(value)
                        lines.append('%s:%s' % (name, value))
                lines.append('')
            # Next
            uid += 1

        return '\n'.join(lines)


    #######################################################################
    # API
    #######################################################################
    def get_record(self, id, sequence=-1):
        if id >= len(self.records):
            return None
        record = self.records[id]
        if record is None:
            return None
        return record[sequence].copy()


    def add_record(self, **kw):
        self.set_changed()
        version = kw.copy()
        self.records = [version]


    def update_record(self, id, **kw):
        self.set_changed()
        version = kw.copy()
        self.records[id].append(version)


    def del_record(self, id):
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
        for id in self.get_record_ids():
            yield self.get_record(id)


