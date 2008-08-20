# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Luis Arturo Belmar-Letelier <luis@itaapy.com>
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from compiler import parse, walk

# Import from itools
from itools.uri import Path, get_absolute_reference2
from text import TextFile
from registry import register_handler_class


class VisitorUnicode(object):

    def __init__(self, filename):
        self.messages = []
        self.filename = filename


    def visitConst(self, const):
        if isinstance(const.value, unicode):
            msg = const.value, {self.filename: [const.lineno]}
            self.messages.append(msg)



class Python(TextFile):

    class_mimetypes = ['text/x-python']
    class_extension = 'py'


    def get_units(self):
        data = self.to_str()
        # Make it work with Windows files (the parser expects '\n' ending
        # lines)
        data = ''.join([ x + '\n' for x in data.splitlines() ])
        # XXX should be improved
        locale_path = get_absolute_reference2('locale').path
        module_path = self.uri.path
        relative_path = locale_path.get_pathto(module_path)
        # Parse and Walk
        ast = parse(data)
        visitor = VisitorUnicode(relative_path)
        walk(ast, visitor)

        return visitor.messages


register_handler_class(Python)
