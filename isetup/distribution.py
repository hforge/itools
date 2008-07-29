# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@itaapy.com>
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
from os import execl, makedirs, chdir, getcwd
from os.path import join, split
from subprocess import call
from sys import executable
from zipfile import ZipFile
from tarfile import open as tar_open, is_tarfile

# Import from itools
from itools.vfs import exists, make_file
from itools.uri import Path

from metadata import egg_info
from repository import EXTENSIONS


class ArchiveNotSupported(Exception):
    """This archive format is not supported"""

class Dist(object):
    """abstract distributions like .egg, .zip, .tar.gz ...
    """

    def __init__(self, location):
        self._metadata = None
        self.fromsetuptools = False
        self.bundle = init_bundle(location)
        self.location = location


    def _init_metadata(self):
        if self._metadata is None:
            pkg_info = self.bundle.find_file('PKG-INFO')
            if pkg_info != None:
                self._metadata = \
                        egg_info(self.bundle.read_file(pkg_info))
            else:
                self._metadata = {}
            setuppy = self.bundle.find_file('setup.py')
            if setuppy != None:
                setuppy_data = self.bundle.read_file(setuppy)
                for line in setuppy_data.splitlines():
                    if 'import' in line and 'setuptools' in line:
                        self.fromsetuptools = True


    def has_metadata(self, metadata):
        self._init_metadata()
        return metadata in self._metadata


    def get_metadata(self, metadata):
        self._init_metadata()
        return self._metadata[metadata]


    def install(self):
        cache_dir = self.location[:-len(Path(self.location).get_name())]
        if not self.bundle.extract(cache_dir):
            raise ArchiveNotSupported

        setup_py_file = self.bundle.find_file('setup.py')
        before = getcwd()
        chdir(split(join(cache_dir, setup_py_file))[0])
        ret = call([executable, 'setup.py', 'install'])
        chdir(before)
        return ret



def init_bundle(location):
    # We will have to rely on extensions ...
    if split(location)[1].endswith('.zip'):
        return ZipBundle(location)
    if split(location)[1].endswith('.tar.gz'):
        return TarBundle(location, 'gzip')
    if split(location)[1].endswith('.tar.bz2'):
        return TarBundle(location, 'bz2')
    if split(location)[1].endswith('.tar'):
        return TarBundle(location, '')
    else:
        raise ArchiveNotSupported



class TarBundle(object):

    # Format can be 'gzip' 'bz2' or ''
    def __init__(self, location, format):
        if format == 'gzip':
            self.handle = tar_open(location, 'r:gz')
        elif format == 'bz2':
            self.handle = tar_open(location, 'r:bz2')
        elif format == '':
            self.handle = tar_open(location, 'r')
        else:
            raise ArchiveNotSupported


    def extract(self, to):
        self.handle.extractall(to)
        return True


    def read_file(self, filename):
        return self.handle.extractfile(filename).read()


    def find_file(self, filename):
        for file in self.handle.getnames():
            if split(file)[1] == filename:
                # why not yield?
                return file
        return None



class ZipBundle(object):

    def __init__(self, location):
        self.handle = ZipFile(location)


    def extract(self, to):
        for f in self.handle.namelist():
            ext_dir = split(join(to, f))[0]
            if not exists(ext_dir):
                makedirs(ext_dir)
            if not exists(join(to, f)):
                make_file(join(to, f))
                out = open(join(to, f), 'w+b')
                out.write(self.handle.read(f))
                out.close()
        return True


    def read_file(self, filename):
        return self.handle.read(filename)


    def find_file(self, filename):
        for file in self.handle.namelist():
            if split(file)[1] == filename:
                # why not yield?
                return file
        return None

