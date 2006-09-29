# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from datetime import datetime
import os
from subprocess import call

# Import from itools
from api import READ, WRITE
from base import BaseFS
from registry import register_file_system


class FileFS(BaseFS):

    @staticmethod
    def exists(reference):
        path = str(reference.path)
        return os.path.exists(path)


    @staticmethod
    def is_file(reference):
        path = str(reference.path)
        return os.path.isfile(path)


    @staticmethod
    def is_folder(reference):
        path = str(reference.path)
        return os.path.isdir(path)


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
        ctime = os.path.getctime(path)
        return datetime.fromtimestamp(ctime)


    @staticmethod
    def get_mtime(reference):
        path = str(reference.path)
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime)


    @staticmethod
    def get_atime(reference):
        path = str(reference.path)
        atime = os.path.getatime(path)
        return datetime.fromtimestamp(atime)


    @staticmethod
    def get_size(reference):
        path = str(reference.path)
        return os.path.getsize(path)


    @staticmethod
    def make_file(reference):
        path = str(reference.path)
        if os.path.exists(path):
            raise OSError, "File exists: '%s'" % reference
        return file(path, 'w')


    @staticmethod
    def make_folder(reference):
        path = str(reference.path)
        os.mkdir(path)


    @staticmethod
    def remove(reference):
        path = str(reference.path)
        if not os.path.exists(path):
            raise OSError, "File does not exist '%s'" % reference

        if os.path.isdir(path):
            # Remove folder contents
            for root, folders, files in os.walk(path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in folders:
                    os.rmdir(os.path.join(root, name))
            # Remove the folder itself
            os.rmdir(path)
        else:
            os.remove(path)


    @staticmethod
    def open(reference, mode=None):
        path = str(reference.path)
        if not os.path.exists(path):
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
        # Open for write
        return file(path, 'r+b')


    @staticmethod
    def copy(source, target):
        # XXX Windows (and maybe other platforms) is not supported, yet
        try:
            status = call(['cp', '-r', str(source.path), str(target.path)])
        except OSError:
            raise NotImplementedError
        if status != 0:
            raise IOError


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
    @staticmethod
    def get_names(reference):
        path = str(reference.path)
        return os.listdir(path)



register_file_system('file', FileFS)
