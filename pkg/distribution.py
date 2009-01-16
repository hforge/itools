# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from Standard Library
from os import chdir, getcwd
from os.path import join, split
from subprocess import call
from sys import executable
from tarfile import TarError
from zipfile import error as zip_error, LargeZipFile

# Import from itools
from itools.handlers import get_handler, TARFile, ZIPFile
from itools.uri import Path
from metadata import PKGINFOFile


class ArchiveNotSupported(Exception):
    """Raised when unable to open an archive
    """



class Bundle(object):
    """Abstract distributions like .egg, .zip, .tar.gz ...
    """

    def __init__(self, location):
        self.location = location

        # The handler
        self.handler = get_handler(location)
        if not isinstance(self.handler, (TARFile, ZIPFile)):
            raise ArchiveNotSupported

        # Metadata
        pkg_info = self.find_lowest_file('PKG-INFO')
        if pkg_info is None:
            self.metadata = PKGINFOFile()
        else:
            data = self.handler.get_file(pkg_info)
            self.metadata = PKGINFOFile(string=data)

        # Setuptools
        self.fromsetuptools = False
        setuppy = self.find_lowest_file('setup.py')
        if setuppy is not None:
            setuppy_data = self.handler.get_file(setuppy)
            for line in setuppy_data.splitlines():
                if 'import' in line and 'setuptools' in line:
                    self.fromsetuptools = True
                    break


    def has_metadata(self, metadata):
        return metadata in self.metadata.attrs.keys()


    def get_metadata(self, metadata):
        return self.metadata.attrs[metadata]


    def safe_get_metadata(self, metadata):
        if not self.has_metadata(metadata):
            return None
        return self.metadata.attrs[metadata]


    def install(self):
        cache_dir = self.location[:-len(Path(self.location).get_name())]
        try:
            self.handler.extract_to_folder(cache_dir)
        except (zip_error, LargeZipFile, TarError):
            return -1

        setup_py_file = self.find_lowest_file('setup.py')
        before = getcwd()
        chdir(split(join(cache_dir, setup_py_file))[0])
        ret = call([executable, 'setup.py', 'install'])
        chdir(before)
        return ret


    def find_lowest_file(self, filename):
        files = [
            x for x in self.handler.contents() if split(x)[1] == filename ]
        if len(files) == 0:
            return None

        files.sort(lambda x, y: cmp(len(x), len(y)))
        return files[0]

