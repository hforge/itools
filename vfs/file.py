# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from os import listdir, makedirs, mkdir, remove, rmdir, walk
from os.path import (exists, getatime, getctime, getmtime, getsize, isfile,
    isdir, join)
from subprocess import call

# Import from itools
from itools.uri import Path, Reference
from vfs import READ, WRITE, APPEND
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
        st_mode = os.stat(path).st_mode
        # Folder
        if st_mode & 0040000:
            return st_mode & 5
        # File
        elif st_mode & 0100000:
            return st_mode & 4
 
        return False


    @staticmethod
    def can_write(reference):
        path = str(reference.path)
        return os.stat(path).st_mode & 2


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
        return file(file_path, 'w')


    @staticmethod
    def make_folder(reference):
        path = str(reference.path)
        mkdir(path)


    @staticmethod
    def remove(reference):
        if isinstance(reference, Reference):
            path = str(reference.path)
        elif isinstance(reference, Path):
            path = str(path)

        if not exists(path):
            raise OSError, "File does not exist '%s'" % reference

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

        # Open for write if possible, otherwise for read
        if mode is None:
            try:
                return file(path, 'r+b')
            except IOError:
                return file(path, 'rb')

        # Open for read
        if mode == READ:
            return file(path, 'rb')
        # Open for append
        if mode == APPEND:
            return file(path, 'ab')
        # Open for write
        return file(path, 'r+b')


    @staticmethod
    def move(source, target):
        # XXX Windows (and maybe other platforms) is not supported, yet
        try:
            status = call(['mv', str(source.path), str(target.path)])
        except OSError:
            raise NotImplementedError
        if status != 0:
            raise IOError


    ######################################################################
    # Folders only
    @classmethod
    def get_names(cls, reference):
        path = str(reference.path)
        return listdir(path)



register_file_system('file', FileFS)
