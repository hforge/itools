# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
# Copyright (C) 2010 David Versmisse <versmisse@lil.univ-littoral.fr>
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

# Import from the Standard Library
from datetime import datetime
from os import listdir, makedirs, remove as os_remove, renames, walk
from os import access, R_OK, W_OK
from os.path import exists, getatime, getctime, getmtime, getsize
from os.path import isfile, isdir, join, basename, dirname
from os.path import abspath, relpath
from shutil import rmtree, copytree, copy as shutil_copy
import mimetypes


# Import from itools
from itools.uri import Path
from .common import WRITE, READ_WRITE, APPEND, READ, get_mimetype


MODES = {WRITE: 'w+', READ_WRITE: 'w+', APPEND: 'a+', READ: 'rb'}


class LocalFolder(object):

    def __init__(self, path='.'):
        if not exists(path):
            raise IOError("No such directory: '%s'" % path)
        if isfile(path):
            raise IOError("Is a directory: '%s'" % path)
        self.path = Path(abspath(path))


    def _resolve_path(self, path):
        path = self.path.resolve2(path)
        return str(path)


    #######################################################################
    # Public API
    #######################################################################
    def exists(self, path):
        path = self._resolve_path(path)
        return exists(path)


    def is_file(self, path):
        path = self._resolve_path(path)
        return isfile(path)


    def is_folder(self, path):
        path = self._resolve_path(path)
        return isdir(path)


    def can_read(self, path):
        path = self._resolve_path(path)
        return access(path, R_OK)


    def can_write(self, path):
        path = self._resolve_path(path)
        return access(path, W_OK)

    def make_file(self, path):
        path = self._resolve_path(path)
        parent_path = dirname(path)
        if exists(parent_path):
            if exists(path):
                raise OSError("File exists: '%s'" % path)
        else:
            makedirs(parent_path)
        return open(path, 'w')

    def make_folder(self, path):
        path = self._resolve_path(path)
        return makedirs(path)

    def get_ctime(self, path):
        path = self._resolve_path(path)
        ctime = getctime(path)
        return datetime.fromtimestamp(ctime)


    def get_mtime(self, path):
        path = self._resolve_path(path)
        mtime = getmtime(path)
        return datetime.fromtimestamp(mtime)


    def get_atime(self, path):
        path = self._resolve_path(path)
        atime = getatime(path)
        return datetime.fromtimestamp(atime)


    def get_mimetype(self, path):
        path = self._resolve_path(path)
        # Not a file ?
        if not isfile(path):
            return 'application/x-not-regular-file'
        name = basename(path)
        return get_mimetype(name)


    def get_size(self, path):
        path = self._resolve_path(path)
        return getsize(path)

    def open(self, path, mode=None):
        path = self._resolve_path(path)
        if isdir(path):
            return self.__class__(path)
        mode = MODES.get(mode, 'r')
        try:
            open(path, mode).read()
        except UnicodeDecodeError:
            return open(path, "rb")
        return open(path, mode)

    def remove(self, path):
        path = self._resolve_path(path)
        print(path)
        if isdir(path):
            # Remove folder contents
            rmtree(path)
        else:
            try:
                os_remove(path)
                print("% s removed successfully" % path)
            except OSError as error:
                print(error)
                print("File path can not be removed")


    def copy(self, source, target):
        source = self._resolve_path(source)
        target = self._resolve_path(target)
        if isdir(source):
            # Copy inside target
            if exists(target):
                target = join(target, basename(source))
            copytree(source, target)
        else:
            # Will overwrite target file
            shutil_copy(source, target)


    def move(self, source, target):
        source = self._resolve_path(source)
        target = self._resolve_path(target)
        return renames(source, target)


    def get_names(self, path='.'):
        path = self._resolve_path(path)
        try:
            return listdir(path)
        except OSError as e:
            # Path does not exist or is not a directory
            if e.errno == 2 or e.errno == 20:
                return []
            raise


    def traverse(self, path='.'):
        path = self._resolve_path(path)
        if not exists(path):
            raise IOError("No such directory: '%s'" % path)
        yield path
        if isdir(path):
            for root, folders, files in walk(path, topdown=True):
                for name in folders:
                    yield join(root, name)
                for name in files:
                    yield join(root, name)


    def get_absolute_path(self, path='.'):
        path = self._resolve_path(path)
        return abspath(path)


    def get_relative_path(self, path):
        path = self._resolve_path(path)
        return relpath(path, start=str(self.path))


    #######################################################################
    # Used by itools.handlers
    #######################################################################
    @staticmethod
    def get_basename(path):
        if type(path) is not Path:
            path = Path(path)
        return path.get_name()


    @staticmethod
    def get_path(path):
        if type(path) is not Path:
            path = Path(path)
        return str(path)


    @staticmethod
    def resolve(base, path):
        if type(base) is not Path:
            base = Path(base)
        path = base.resolve(path)
        return str(path)


    @staticmethod
    def resolve2(base, path):
        if type(base) is not Path:
            base = Path(base)
        path = base.resolve2(path)
        return str(path)


    # Resolution method for handler database keys
    normalize_key = get_absolute_path


# The entrypoint is the current working directory
lfs = LocalFolder()
