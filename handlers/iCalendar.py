# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from itools
from Text import Text



def get_lines(data):
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


NAME, PNAME, PVALUE, VALUE = range(4)

def parse_line(line):
    """
    Parses a parameter string (e.g. p1=v1;p2=v2) and returns the pairs
    name, value.
    """
    state = 0
    for c in line:
        if state == 0:
            if c.isalnum() or c == '-':
                lexeme = c
                state = 1
            else:
                raise ValueError
        elif state == 1:
            if c.isalnum() or c == '-':
                lexeme += c
            elif c == ';':
                yield NAME, lexeme
                lexeme, state = '', 2
            elif c == ':':
                yield NAME, lexeme
                lexeme, state = c, 8
            else:
                raise ValueError
        elif state == 2:
            if c.isalnum() or c == '-':
                lexeme, state = c, 3
            else:
                raise ValueError
        elif state == 3:
            if c.isalnum() or c == '-':
                lexeme += c
            elif c == '=':
                yield PNAME, lexeme
                lexeme, state = '', 4
            else:
                raise ValueError
        elif state == 4:
            if c == '"':
                state = 6
            elif c not in (';', ':', ','):
                lexeme, state = c, 5
            else:
                raise ValueError
        elif state == 5:
            if c == ';':
                yield PVALUE, lexeme
                lexeme, state = '', 2
            elif c == ':':
                yield PVALUE, lexeme
                lexeme, state = '', 8
            elif c not in ('"', ','):
                lexeme += c
            else:
                raise ValueError
        elif state == 6:
            if c == '"':
                state = 7
            else:
                lexeme += c
        elif state == 7:
            if c == ';':
                yield PVALUE, lexeme
                lexeme, state = '', 2
            elif c == ':':
                yield PVALUE, lexeme
                lexeme, state = '', 8
            else:
                raise ValueError
        elif state == 8:
            lexeme += c

    yield VALUE, lexeme



class iCalendar(Text):
    def _load(self):
        Text._load(self)

        for line in get_lines(self._data):
            line = list(parse_line(line))
            # Extract the property name
            name = line[0][1]
            i = 1
            # Extract the parameters
            params = {}
            while line[i][0] == PNAME:
                params[line[i][1]] = line[i+1][1]
                i += 2
            # Extract the property value
            value = line[i][1]

        del self._data
