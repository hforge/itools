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
from os import makedirs, chdir, getcwd
from os.path import join, split
from subprocess import call
from sys import executable
from tarfile import open as tar_open, TarError
from tempfile import TemporaryFile
from zipfile import ZipFile, error as zip_error, LargeZipFile

# Import from itools
from itools.uri import Path
from itools.vfs import exists, make_file
from metadata import PKGINFOFile
from repository import EXTENSIONS


class ArchiveNotSupported(Exception):
    """Raised when unable to open an archive
    """



class Bundle(object):
    """Abstract distributions like .egg, .zip, .tar.gz ...
    """

    def __init__(self, location):
        self.location = location

        # Init handle
        self.init_handle(location, format)

        # Metadata
        pkg_info = self.find_lowest_file('PKG-INFO')
        if pkg_info is None:
            self.metadata = PKGINFOFile()
        else:
            data = self.get_file(pkg_info).read()
            self.metadata = PKGINFOFile(string=data)

        # Setuptools
        self.fromsetuptools = False
        setuppy = self.find_lowest_file('setup.py')
        if setuppy is not None:
            setuppy_data = self.read_file(setuppy)
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
            self.extract(cache_dir)
        except (zip_error, LargeZipFile, TarError):
            return -1

        setup_py_file = self.find_lowest_file('setup.py')
        before = getcwd()
        chdir(split(join(cache_dir, setup_py_file))[0])
        ret = call([executable, 'setup.py', 'install'])
        chdir(before)
        return ret


    def find_lowest_file(self, filename):
        files = [f for f in self.handle.getnames() if split(f)[1] == filename]
        files.sort(lambda x, y: cmp(len(x), len(y)))
        if len(files) > 0:
            return files[0]
        return None


    #######################################################################
    # Abstract API
    def init_handle(self, location, format):
        raise NotImplementedError


    def extract(self, to):
        raise NotImplementedError


    def read_file(self, filename):
        raise NotImplementedError


    def get_file(self, filename):
        raise NotImplementedError



class TarBundle(Bundle):
    mode = 'r'

    # Format can be 'gzip' 'bz2' or ''
    def init_handle(self, location, format):
        self.handle = tar_open(location, self.mode)


    def extract(self, to):
        self.handle.extractall(to)


    def read_file(self, filename):
        return self.handle.extractfile(filename).read()


    def get_file(self, filename):
        return self.handle.extractfile(filename)



class TGZBundle(TarBundle):
    mode = 'r:gz'



class TBZ2Bundle(TarBundle):
    mode = 'r:bz2'



class ZipBundle(Bundle):

    def init_handle(self, location, format):
        self.handle = ZipFile(location)


    def extract(self, to):
        for file in self.handle.namelist():
            path = join(to, file)
            ext_dir = split(path)[0]
            if not exists(ext_dir):
                makedirs(ext_dir)
            if not exists(path):
                make_file(path)
                out = open(path, 'w+b').write(self.handle.read(file))


    def read_file(self, filename):
        return self.handle.read(filename)


    def get_file(self, filename):
        handler = TemporaryFile()
        handler.write(self.handle.read(filename))
        return handler



def get_bundle(location):
    filename = split(location)[1]
    if filename.endswith('.zip'):
        return ZipBundle(location)
    elif filename.endswith('.tar.gz'):
        return TGZBundle(location, 'gzip')
    elif filename.endswith('.tar.bz2'):
        return TBZ2Bundle(location, 'bz2')
    elif filename.endswith('.tar'):
        return TarBundle(location, '')
    else:
        raise ArchiveNotSupported
