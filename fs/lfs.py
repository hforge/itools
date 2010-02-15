# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@itaapy.com>

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
from os import listdir, makedirs, remove as os_remove, walk
from os import access, R_OK, W_OK
from os.path import exists, getatime, getctime, getmtime ,getsize
from os.path import isfile, isdir, join, basename, dirname
from os.path import abspath, relpath, normpath
from shutil import rmtree, copytree, copy as shutil_copy, move as shutil_move

# Import from itools
from common import WRITE, READ_WRITE, APPEND, READ, get_mimetype


MODES = {WRITE: 'wb', READ_WRITE: 'r+b', APPEND: 'ab', READ: 'rb'}


######################################################################
# Public API
######################################################################
class LocalFolder(object):

    def __init__(self, path='.'):
        if not exists(path):
            raise IOError, "No such directory: '%s'" % path
        if isfile(path):
            raise IOError, "Is a directory: '%s'" % path
        self.path = abspath(normpath(path))


    def _resolve_path(self, path):
        path = join(self.path, path)
        return normpath(path)


    ############################
    # Public API
    ############################
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
                raise OSError, "File exists: '%s'" % path
        else:
            makedirs(parent_path)
        return file(path, 'wb')


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
        mode = MODES.get(mode, 'rb')
        return file(path, mode)


    def remove(self, path):
        path = self._resolve_path(path)
        if isdir(path):
            # Remove folder contents
            rmtree(path)
        else:
            os_remove(path)


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
        # If target is a folder, move inside it
        return shutil_move(source, target)


    def get_names(self, path='.'):
        path = self._resolve_path(path)
        return listdir(path)


    def traverse(self, path):
        path = self._resolve_path(path)
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

    # Alias to match vfs API (URI makes no sense for paths)
    get_uri = get_absolute_path


    def get_relative_path(self, path):
        path = self._resolve_path(path)
        return relpath(path)


    @staticmethod
    def resolve(base, reference):
        endswith_slash = base[-1] == '/'
        base = abspath(base)
        # '/a/b/' + 'c' => '/a/b/c'
        if endswith_slash:
            return join(base, reference)
        return join(dirname(base), reference)
        # '/a/b' + 'c' => '/a/c'


    @staticmethod
    def resolve2(base, reference):
        base = abspath(base)
        # '/a/b' + 'c' => '/a/b/c'
        # '/a/b/' + 'c' => '/a/b/c'
        return join(base, reference)


# The entrypoint is the current working directory
lfs = LocalFolder()
