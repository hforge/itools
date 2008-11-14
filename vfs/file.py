# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
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
from os import (listdir, makedirs, mkdir, remove, rename, rmdir, stat, walk,
                access, R_OK, W_OK)
from os.path import (exists, getatime, getctime, getmtime, getsize, isfile,
    isdir, join)
from subprocess import call

# Import from itools
from itools.uri import Path, Reference
from vfs import READ, WRITE, READ_WRITE, APPEND, copy
from base import BaseFS
from registry import register_file_system


class FileFS(BaseFS):

    @staticmethod
    def exists(reference):
        path = str(reference.path)
        return exists(path)


    @staticmethod
    def is_file(reference):
        path = str(reference.path)
        return isfile(path)


    @classmethod
    def is_folder(cls, reference):
        path = str(reference.path)
        return isdir(path)


    @staticmethod
    def can_read(reference):
        path = str(reference.path)
        return access(path, R_OK)


    @staticmethod
    def can_write(reference):
        path = str(reference.path)
        return access(path, W_OK)


    @staticmethod
    def get_ctime(reference):
        path = str(reference.path)
        ctime = getctime(path)
        return datetime.fromtimestamp(ctime)


    @staticmethod
    def get_mtime(reference):
        path = str(reference.path)
        mtime = getmtime(path)
        return datetime.fromtimestamp(mtime)


    @staticmethod
    def get_atime(reference):
        path = str(reference.path)
        atime = getatime(path)
        return datetime.fromtimestamp(atime)


    @staticmethod
    def get_size(reference):
        path = str(reference.path)
        return getsize(path)


    @staticmethod
    def make_file(reference):
        folder_path = str(reference.path[:-1])
        file_path = str(reference.path)

        if exists(folder_path):
            if exists(file_path):
                raise OSError, "File exists: '%s'" % reference
        else:
            makedirs(folder_path)
        return file(file_path, 'wb')


    @staticmethod
    def make_folder(reference):
        path = str(reference.path)
        makedirs(path)


    @staticmethod
    def remove(path):
        if isinstance(path, Reference):
            path = str(path.path)
        elif isinstance(path, Path):
            path = str(path)

        if not exists(path):
            raise OSError, "File does not exist '%s'" % path

        if isdir(path):
            # Remove folder contents
            for root, folders, files in walk(path, topdown=False):
                for name in files:
                    remove(join(root, name))
                for name in folders:
                    rmdir(join(root, name))
            # Remove the folder itself
            rmdir(path)
        else:
            remove(path)


    @staticmethod
    def open(reference, mode=None):
        path = str(reference.path)
        if not exists(path):
            raise OSError, "File does not exist '%s'" % reference

        # Open for write
        if mode == WRITE:
            return file(path, 'wb')
        # Open for read/write
        if mode == READ_WRITE:
            return file(path, 'r+b')
        # Open for append
        if mode == APPEND:
            return file(path, 'ab')
        # Open for read (default)
        return file(path, 'rb')


    @staticmethod
    def move(source, target):
        # Fail if target exists and is a file
        dst = str(target.path)
        if isfile(dst):
            raise OSError, '[Errno 20] Not a directory'

        # If target is a folder, move inside it
        if isdir(dst):
            dst = target.path.resolve2(source.path[-1])
            dst = str(dst)

        src = str(source.path)
        try:
            rename(src, dst)
        except OSError:
            copy(src, dst)
            FileFS.remove(src)


    ######################################################################
    # Folders only
    @classmethod
    def get_names(cls, reference):
        path = str(reference.path)
        return listdir(path)



register_file_system('file', FileFS)
