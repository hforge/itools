# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from text import Text



class Config(Text):

    """
    The data structure of this handler is:
        
      self.lines:
        [None, <block>, None, None, <block>]

    Where "None" is a blank line, and block is a tuple:

        ([comment_line_1, ..., comment_line_n], <variable>)

    A comment is stored as list of strings, one for every comment line. The
    variable may be None (then the comment is isolated), or a tuple with the
    variable name and value.

    The "values" data structure is:
        
        self.values:
            {<var name>: line no}

    This is, a mapping from the name of the variable to a reference to the
    "self.lines" data structure, from which we will retrieve the variable
    value and associated comment.
    """

    class_extension = None


    __slots__ = ['database', 'uri', 'timestamp', 'parent', 'name',
                 'real_handler', 'lines', 'values']


    def new(self, **kw):
        # Comments are not supported here
        self.values = {}
        self.lines = []

        n = 0
        for name, value in kw.items():
            # Add the variable, with an empty comment
            self.lines.append(([], (name, value)))
            # Separate with a blank line
            self.lines.append(None)
            # Keep reference from the variable name
            self.values[name] = n
            # Next
            n += 2


    def _load_state_from_file(self, file):
        values = {}
        lines = []

        line = file.readline()
        while line:
            line = line.strip()
            if not line:
                # Blank
                lines.append(None)
                # Next line
                line = file.readline()
            elif line[0] == '#':
                # Just a comment, or a comment with a variable
                comment = [line.lstrip('#').strip()]
                # Parse the comment
                line = file.readline()
                while True:
                    line_stripped = line.strip()
                    if not line_stripped.startswith('#'):
                        break
                    comment.append(line_stripped.lstrip('#').strip())
                    line = file.readline()

                # Is there a variable?
                if line_stripped:
                    # Parse the variable
                    name, value = line.split('=', 1)
                    name = name.strip()
                    value = value.strip()
                    # Update the data structure
                    lines.append((comment, (name, value)))
                    values[name] = len(lines) - 1
                    # Next
                    line = file.readline()
                else:
                    # A solitary comment 
                    lines.append((comment, None))
            else:
                # Variable without a comment
                name, value = line.split('=', 1)
                name = name.strip()
                value = value.strip()
                lines.append(([], (name, value)))
                values[name] = len(lines) - 1
                # Next line
                line = file.readline()

        self.lines = lines
        self.values = values


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
            return default
        # Get the line
        n = self.values[name]
        line = self.lines[n]
        # Return the variable value
        value = line[1][1]
        if type is None:
            return value
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
