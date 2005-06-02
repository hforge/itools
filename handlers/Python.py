# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 J. David Ibáñez <jdavid@itaapy.com>
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

# Import from the Standard Library
import compiler

# Import from itools
from Text import Text


class Visitor(object):

    def __init__(self):
        self.messages = []


    def visitConst(self, const):
        if isinstance(const.value, unicode):
            self.messages.append((const.value, const.lineno))


class Python(Text):

    class_mimetypes = ['text/x-python']
    class_extension = 'py'
    class_version = '20040625'


    def get_messages(self):
        ast = compiler.parse(self.to_str())
        visitor = Visitor()
        compiler.walk(ast, visitor)
        return visitor.messages


Text.register_handler_class(Python)
