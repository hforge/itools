# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
import mimetypes
from zipfile import ZipFile
from tarfile import open as open_tarfile
from cStringIO import StringIO

# Import from itools
from file import File
from registry import register_handler_class


class ZIPFile(File):

    class_mimetypes = ['application/zip']
    class_extension = 'zip'

    def get_contents(self):
        archive = StringIO(self.to_str())
        zip = ZipFile(archive)
        contents = zip.namelist()
        zip.close()
        return contents


    def get_file(self, filename):
        archive = StringIO(self.to_str())
        zip = ZipFile(archive)
        contents = zip.read(filename)
        zip.close()
        return contents



class TARFile(File):

    class_mimetypes = ['application/x-tar']
    class_extension = 'tar'

    def get_contents(self):
        name = self.uri.path[-1]
        archive = StringIO(self.to_str())
        tar = open_tarfile(name=name, fileobj=archive)
        contents = tar.getnames()
        tar.close()

        return contents


class GzipFile(File):

    class_mimetypes = ['application/x-gzip']
    class_extension = 'gz'


class Bzip2File(File):

    class_mimetypes = ['application/x-bzip2']
    class_extension = 'bz2'


# Register
for handler_class in [ZIPFile, TARFile, GzipFile, Bzip2File]:
    register_handler_class(handler_class)

# Mimetypes BZip2 support
mimetypes.suffix_map['.tbz2'] = '.tar.bz2'
mimetypes.encodings_map['.bz2'] = 'bzip2'
mimetypes.add_type('application/x-tar', '.tar.bz2')
