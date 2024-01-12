# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2006-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from os.path import join
from zipfile import ZipFile
from tarfile import open as open_tarfile
from io import StringIO, BytesIO

# Import from itools
from .file import File
from .registry import register_handler_class


class Info(object):

    __slots__ = ['name', 'mtime']

    def __init__(self, name, mtime):
        self.name = name
        # XXX This datetime is naive because (apparently) neither ZIP nor TAR
        # archives keep the timezone, so this field is mostly useless
        self.mtime = mtime


class ZIPFile(File):

    class_mimetypes = ['application/zip']
    class_extension = 'zip'

    def _open_zipfile(self):
        data = self.to_str()
        if isinstance(data, bytes):
            archive = BytesIO(data)
        elif isinstance(data, str):
            archive = StringIO(data)
        else:
            raise Exception("Error Zipfile")
        return ZipFile(archive)

    def get_members(self):
        zip = self._open_zipfile()
        try:
            names = zip.namelist()
            names.sort()
            for name in names:
                member = zip.getinfo(name)
                mtime = datetime(*(member.date_time))
                yield Info(name, mtime)
        finally:
            zip.close()

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
                data = zip.read(filename)
                path = join(dst, filename)
                handler = File(string=data)
                self.database.set_handler(path, handler)
        finally:
            zip.close()


class TARFile(File):

    class_mimetypes = ['application/x-tar']
    class_extension = 'tar'
    class_mode = 'r'

    def _open_tarfile(self):
        archive = StringIO(self.to_str())
        return open_tarfile(mode=self.class_mode, fileobj=archive)

    def get_members(self):
        tar = self._open_tarfile()
        try:
            names = tar.getnames()
            names.sort()
            for name in names:
                member = tar.getmember(name)
                if member.isdir():
                    name = f'{name}/'
                mtime = datetime.utcfromtimestamp(member.mtime)
                yield Info(name, mtime)
        finally:
            tar.close()

    def get_contents(self):
        tar = self._open_tarfile()
        try:
            names = tar.getnames()
            # Append trailing slash to directories, as it is with Zip files
            return [
                f'{x}/' if tar.getmember(x).isdir() else x for x in names ]
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
