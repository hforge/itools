# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
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
from itools.core import has_encoding, has_extension
from itools.datatypes import DataType
from itools.i18n import has_language


class FileName(DataType):
    """A filename is tuple consisting of a name, a type and a language.
    """
    # TODO Consider the compression encoding (gzip, ...)
    # TODO Consider the character encoding (utf-8, ...)

    @staticmethod
    def decode(data):
        parts = data.rsplit('.', 1)
        # Case 1: name
        if len(parts) == 1:
            return data, None, None

        name, ext = parts
        # Case 2: name.encoding
        if has_encoding(ext):
            return name, ext, None

        if '.' in name:
            a, b = name.rsplit('.', 1)
            if has_extension(b) and has_language(ext):
                # Case 3: name.type.language
                return a, b, ext
        if has_extension(ext):
            # Case 4: name.type
            return name, ext, None
        elif has_language(ext):
            # Case 5: name.language
            return name, None, ext

        # Case 1: name
        return data, None, None


    @staticmethod
    def encode(value):
        name, type, language = value
        if type is not None:
            name = name + '.' + type
        if language is not None:
            name = name + '.' + language
        return name


