# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Luis Arturo Belmar-Letelier <luis@itaapy.com>
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Matthieu France <matthieu@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
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
try:
    from ast import parse, NodeVisitor
except ImportError:
    # Python 2.5
    from compiler import parse, walk
    NodeVisitor = object
else:
    # Python 2.6
    def walk(ast, visitor):
        visitor.generic_visit(ast)

# Import from itools
from itools.handlers import TextFile, register_handler_class
from itools.srx import TEXT



class VisitorUnicode(NodeVisitor):

    def __init__(self):
        self.messages = []


    def visit_Str(self, node):
        value = node.s
        if type(value) is unicode and value.strip():
            # Context = None
            msg = ((TEXT, value),), None, node.lineno
            self.messages.append(msg)


    # Python 2.5
    def visitConst(self, node):
        value = node.value
        if type(value) is unicode and value.strip():
            # Context = None
            msg = ((TEXT, value),), None, node.lineno
            self.messages.append(msg)



class Python(TextFile):

    class_mimetypes = ['text/x-python']
    class_extension = 'py'


    def get_units(self, srx_handler=None):
        data = self.to_str()
        # Make it work with Windows files (the parser expects '\n' ending
        # lines)
        data = ''.join([ x + '\n' for x in data.splitlines() ])
        # Parse and Walk
        ast = parse(data)
        visitor = VisitorUnicode()
        walk(ast, visitor)
        return visitor.messages


# Register
register_handler_class(Python)
