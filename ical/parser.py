# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Nicolas Deram <nderam@itaapy.com>
#               2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
  

###################################################################
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
###################################################################
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



def parse(data):
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


