# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# Import from itools
from itools.core import guess_type, has_encoding, has_extension
from itools.datatypes import DataType
from itools.i18n import has_language


READ = 'r'
WRITE = 'w'
READ_WRITE = 'w+'
APPEND = 'a+'


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


def get_mimetype(name):
    """Try to guess the mimetype given the name. To guess from the name we
    need to extract the type extension, we use an heuristic for this task,
    but it needs to be improved because there are many patterns:

    <name>                                 README
    <name>.<type>                          index.html
    <name>.<type>.<language>               index.html.en
    <name>.<type>.<language>.<encoding>    index.html.en.UTF-8
    <name>.<type>.<compression>            itools.tar.gz
    etc...

    And even more complex, the name could contain dots, or the filename
    could start by a dot (a hidden file in Unix systems).
    """
    name, extension, language = FileName.decode(name)
    # Figure out the mimetype from the filename extension
    if extension is not None:
        mimetype, encoding = guess_type('%s.%s' % (name, extension))
        # FIXME Compression schemes are not mimetypes, see /etc/mime.types
        if encoding == 'gzip':
            if mimetype == 'application/x-tar':
                return 'application/x-tgz'
            return 'application/x-gzip'
        elif encoding == 'bzip2':
            if mimetype == 'application/x-tar':
                return 'application/x-tbz2'
            return 'application/x-bzip2'
        elif mimetype is not None:
            return mimetype

    return 'application/octet-stream'
