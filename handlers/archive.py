# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os.path import join
from zipfile import ZipFile
from tarfile import open as open_tarfile
from cStringIO import StringIO

# Import from itools
from itools.uri import get_uri_name
from file import File
from registry import register_handler_class
from itools import vfs


class ZIPFile(File):

    class_mimetypes = ['application/zip']
    class_extension = 'zip'


    def _open_zipfile(self):
        archive = StringIO(self.to_str())
        return ZipFile(archive)


    def get_contents(self):
        zip = self._open_zipfile()
        try:
            return zip.namelist()
        finally:
            zip.close()


    def get_file(self, filename):
        zip = self._open_zipfile()
        try:
            return zip.read(filename)
        finally:
            zip.close()


    def extract_to_folder(self, dst):
        zip = self._open_zipfile()
        try:
            for filename in zip.namelist():
                path = join(dst, filename)
                with vfs.make_file(path) as file:
                    file.write(zip.read(filename))
        finally:
            zip.close()



class TARFile(File):

    class_mimetypes = ['application/x-tar']
    class_extension = 'tar'
    class_mode = 'r'


    def _open_tarfile(self):
        name = get_uri_name(self.uri)
        archive = StringIO(self.to_str())
        return open_tarfile(name, self.class_mode, fileobj=archive)


    def get_contents(self):
        tar = self._open_tarfile()
        try:
            return tar.getnames()
        finally:
            tar.close()


    def get_file(self, filename):
        tar = self._open_tarfile()
        try:
            return tar.extractfile(filename).read()
        finally:
            tar.close()


    def extract_to_folder(self, dst):
        tar = self._open_tarfile()
        try:
            tar.extractall(dst)
        finally:
            tar.close()



class TGZFile(TARFile):

    class_mimetypes = ['application/x-tgz']
    class_extension = 'tgz'
    class_mode = 'r:gz'



class TBZ2File(TARFile):

    class_mimetypes = ['application/x-tbz2']
    class_extension = 'tbz2'
    class_mode = 'r:bz2'



class GzipFile(File):

    class_mimetypes = ['application/x-gzip']
    class_extension = 'gz'



class Bzip2File(File):

    class_mimetypes = ['application/x-bzip2']
    class_extension = 'bz2'



# Register
for cls in [ZIPFile, TARFile, TGZFile, TBZ2File, GzipFile, Bzip2File]:
    register_handler_class(cls)

