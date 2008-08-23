# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 Nicolas Deram <nicolas@itaapy.com>
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
from textwrap import wrap

# Import from itools
from itools.datatypes.primitive import String
from text import TextFile


###########################################################################
# Lines Analyser (an automaton)
###########################################################################
BLANK, COMMENT, VAR, VAR_START, VAR_CONT, VAR_END, EOF = range(7)

def get_lines(file):
    """Analyses the physical lines, identifies the type and parses them.
    Every line is returned as a three-elements tuple:

        <type>, <value>, <line number>

    There are six line types:

        BLANK -- made up of white spaces.

        COMMENT -- starts by the sharp character (#).

        VAR -- a variable definition (name and value) in a single line;
          the value may be delimited by double quotes.

        VAR_START -- the first line in a multi-line variable (when the
          value, delimited by double quotes, splits accross several
          physical lines).

        VAR_CONT -- the continuation of a multiline variable.

        VAR_END -- the last physical line in a multiline variable.

    This table shows the line value for every line type:

        BLANK      =>   None
        COMMENT    =>   <line>
        VAR        =>   <name>, <value>
        VAR_START  =>   <name>, <first line>
        VAR_CONT   =>   <line>
        VAR_END    =>   <line>
    """
    state = 0
    line_num = 1

    for line in file.readlines():
        line = line.strip()
        if state == 0:
            # Initial state (waiting a new block)
            if len(line) == 0:
                yield BLANK, None, line_num
            elif line[0] == '#':
                yield COMMENT, line.lstrip('#').strip(), line_num
            elif '=' in line:
                name, value = line.split('=', 1)
                name = name.strip()
                value = value.strip()
                if value and value[0] == '"':
                    if value[-1] == '"' and len(value) > 1:
                        value = value[1:-1]
                        yield VAR, (name, value), line_num
                    else:
                        yield VAR_START, (name, value[1:]), line_num
                        state = 1
                else:
                    yield VAR, (name, value), line_num
            else:
                raise SyntaxError, 'unknown line "%d"' % line_num
        elif state == 1:
            # Multiline value
            if line and line[-1] == '"':
                yield VAR_END, line[:-1], line_num
                state = 0
            else:
                yield VAR_CONT, line, line_num

        # Next
        line_num += 1

    yield EOF, None, line_num



class Lines(object):

    def __init__(self, file):
        self.lines = get_lines(file)
        self.next()


    def next(self):
        self.current = self.lines.next()



###########################################################################
# Blocks Analyser (a grammar)
###########################################################################
def parse(file):
    """This parser is based on an automaton (see above) and a grammar.

    Each production of the grammar is implemented as a function, see
    the function doc strings for the definition of the production they
    implement.
    """
    lines = Lines(file)

    blocks = []
    values = {}
    while lines.current[0] != EOF:
        block = read_block(lines)
        # Semantics: keep the blocks, map from variable names to blocks
        if block is not None:
            comment, variable = block
            if variable is not None:
                name, value = variable
                values[name] = len(blocks)
        blocks.append(block)
    return blocks, values


def read_block(lines):
    """Grammar production:

      BLANK | COMMENT <comment> <variable> | VAR | VAR_START <multiline>

    """
    type, value, line_num = lines.current
    if type == BLANK:
        lines.next()
        return None
    elif type == COMMENT:
        lines.next()
        comment = [value] + read_comment(lines)
        variable = read_variable(lines)
        return comment, variable
    elif type == VAR:
        lines.next()
        return [], value
    elif type == VAR_START:
        name, value = value
        lines.next()
        value = value + '\n' + read_multiline(lines)
        return [], (name, value)
    else:
        raise SyntaxError, 'unexpected line "%d"' % line_num


def read_comment(lines):
    """Grammar production:

      COMMENT <comment> | lambda

    """
    type, value, line_num = lines.current
    if type == COMMENT:
        lines.next()
        return [value] + read_comment(lines)
    return []


def read_variable(lines):
    """Grammar production:

      VAR | VAR_START <multiline> | lambda

    """
    type, value, line_num = lines.current
    if type == VAR:
        lines.next()
        return value
    elif type == VAR_START:
        name, value = value
        lines.next()
        return name, value + '\n' + read_multiline(lines)


def read_multiline(lines):
    """Grammar production:

      VAR_CONT <multiline> | VAR_END

    """
    type, value, line_num = lines.current
    if type == VAR_CONT:
        lines.next()
        return value + '\n' + read_multiline(lines)
    elif type == VAR_END:
        lines.next()
        return value
    else:
        raise SyntaxError, 'unexpected line "%s"' % line_num


###########################################################################
# The handler
###########################################################################
class ConfigFile(TextFile):
    """The data structure of this handler is:

      self.lines:
        [None, <block>, None, None, <block>]

    Where "None" is a blank line, and block is a tuple:

        ([comment_line_1, ..., comment_line_n], <variable>)

    A comment is stored as list of strings, one for every comment line.  The
    variable may be None (then the comment is isolated), or a tuple with the
    variable name and value.

    If the value is a list, then it appears in the source as a multiline
    delimited by double quotes, for example:

      description = "This is an example of a value splitted accross several
        lines, using double quotes as delimiters"

    The "values" data structure is:

        self.values:
            {<var name>: line no}

    This is, a mapping from the name of the variable to a reference to the
    "self.lines" data structure, from which we will retrieve the variable
    value and associated comment.
    """

    class_extension = None
    schema = None


    def new(self, **kw):
        # Comments are not supported here
        self.values = {}
        self.lines = []

        n = 0
        for name, value in kw.items():
            if isinstance(value, str) is False:
                raise TypeError, 'the value must be a string.'
            # Add the variable, with an empty comment
            self.lines.append(([], (name, value)))
            # Separate with a blank line
            self.lines.append(None)
            # Keep reference from the variable name
            self.values[name] = n
            # Next
            n += 2


    def _load_state_from_file(self, file):
        self.lines, self.values = parse(file)


    def to_str(self):
        values = self.values

        names = values.keys()

        lines = []
        for line in self.lines:
            if line is None:
                # Blank line
                lines.append('\n')
            else:
                comment, var = line
                for line in comment:
                    lines.append('# %s\n' % line)
                if var is not None:
                    lines.append('%s = %s\n' % var)

        return ''.join(lines)


    #########################################################################
    # API
    #########################################################################
    def set_value(self, name, value, comment=None):
        """
        Sets a variable with the given value, and optionally a comment.
        """
        if isinstance(comment, str):
            comment = wrap(comment)

        if value is not None:
            if self.schema is not None and name in self.schema:
                value = self.schema[name].encode(value)
            if not isinstance(value, str):
                raise TypeError, 'the value must be a string.'

        self.set_changed()
        if name in self.values:
            n = self.values[name]
            line = self.lines[n]
            if value is None:
                del self.values[name]
                self.lines[n] = None
            else:
                if comment is None:
                    comment = line[0]
                self.lines[n] = comment, (name, value)
        elif value is not None:
            # A new variable
            if comment is None:
                comment = []
            self.lines.append((comment, (name, value)))
            self.values[name] = len(self.lines) - 1
            # Append a blank line
            self.lines.append(None)


    def append_comment(self, comment):
        """
        Appends a solitary comment.
        """
        # The comment should be a list
        if isinstance(comment, str):
            comment = wrap(comment)
        # Change
        self.set_changed()
        self.lines.append((comment, None))
        # Append a blank line
        self.lines.append(None)


    def get_value(self, name, type=None, default=None):
        if name not in self.values:
            if default is not None:
                return default
            elif type is not None and getattr(type, 'default', None):
                return type.default
            elif self.schema is not None and name in self.schema:
                return self.schema[name].default
            return None

        # Get the line
        n = self.values[name]
        line = self.lines[n]
        value = line[1][1]
        if type is None:
            type = String
            if self.schema is not None:
                type = self.schema.get(name, String)

        # Multiple values
        is_multiple = getattr(type, 'multiple', False)
        if is_multiple:
            value = value.split()
            values = [ type.decode(x) for x in value ]
            return values

        return type.decode(value)


    def get_comment(self, name):
        if name not in self.values:
            return None
        # Get the line
        n = self.values[name]
        line = self.lines[n]
        # Return the comment
        return ' '.join(line[0])


    def has_value(self, name):
        return name in self.values
