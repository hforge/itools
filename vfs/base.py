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
from datetime import datetime
from mimetypes import guess_type
from urllib import quote

# Import from itools
from itools.datatypes import FileName



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
        """
        Try to guess the mimetype for a resource, given the resource itself
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

        XXX Use magic numbers too (like file -i).
        """
        name = reference.path[-1]
        # Parse the filename
        name, type, language = FileName.decode(name)

        # Get the mimetype
        if type is not None:
            mimetype, encoding = guess_type('.%s' % type)
            if mimetype is not None:
                return mimetype

        if cls.is_file(reference):
            return 'application/octet-stream'

        return 'application/x-not-regular-file'


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

