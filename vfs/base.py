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

# Import from the Standard Library
from datetime import datetime
import mimetypes
from mimetypes import guess_type
from urllib import quote

# Import from itools
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
        if '.%s' % ext.lower() in mimetypes.encodings_map:
            return name, ext, None

        if '.' in name:
            a, b = name.rsplit('.', 1)
            if '.%s' % b.lower() in mimetypes.types_map and has_language(ext):
                # Case 3: name.type.language
                return a, b, ext
        if '.%s' % ext.lower() in mimetypes.types_map:
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


# Translate compression encoding to mimetype
encoding_map = {'gzip': 'application/x-gzip', 'bzip2': 'application/x-bzip2'}


class BaseFS(object):

    @staticmethod
    def exists(reference):
        raise NotImplementedError


    @staticmethod
    def is_file(reference):
        raise NotImplementedError


    @classmethod
    def is_folder(cls, reference):
        raise NotImplementedError


    @staticmethod
    def can_read(reference):
        raise NotImplementedError


    @staticmethod
    def can_write(reference):
        raise NotImplementedError


    @staticmethod
    def get_ctime(reference):
        raise NotImplementedError


    @staticmethod
    def get_mtime(reference):
        raise NotImplementedError


    @staticmethod
    def get_atime(reference):
        raise NotImplementedError


    @classmethod
    def get_mimetype(cls, reference):
        """Try to guess the mimetype for a resource, given the resource itself
        and its name. To guess from the name we need to extract the type
        extension, we use an heuristic for this task, but it needs to be
        improved because there are many patterns:

        <name>                                 README
        <name>.<type>                          index.html
        <name>.<type>.<language>               index.html.en
        <name>.<type>.<language>.<encoding>    index.html.en.UTF-8
        <name>.<type>.<compression>            itools.tar.gz
        etc...

        And even more complex, the name could contain dots, or the filename
        could start by a dot (a hidden file in Unix systems).
        """
        # TODO Use magic numbers too (like file -i).
        if not cls.is_file(reference):
            return 'application/x-not-regular-file'

        # Find out the filename extension
        name = reference.path[-1]
        name, extension, language = FileName.decode(name)
        # Figure out the mimetype from the filename extension
        if extension is not None:
            mimetype, encoding = guess_type('.%s' % extension)
            if encoding is not None:
                if encoding in encoding_map:
                    return encoding_map[encoding]
            elif mimetype is not None:
                return mimetype

        return 'application/octet-stream'


    @staticmethod
    def make_file(reference):
        raise NotImplementedError


    @staticmethod
    def make_folder(reference):
        raise NotImplementedError


    @staticmethod
    def remove(reference):
        raise NotImplementedError


    @staticmethod
    def open(reference, mode=None):
        raise NotImplementedError


    @staticmethod
    def move(source, target):
        raise NotImplementedError


    ######################################################################
    # Folders only
    @classmethod
    def get_names(cls, reference):
        raise NotImplementedError


    @classmethod
    def traverse(cls, reference):
        stack = [reference]
        while stack:
            folder = stack.pop()
            yield folder
            try:
                names = cls.get_names(folder)
            except OSError:
                # Don't traverse the folder if we can't (e.g. no permissions)
                continue

            for name in names:
                name = quote(name)
                ref = folder.resolve2(name)
                if cls.is_folder(ref):
                    stack.append(ref)
                else:
                    yield ref

