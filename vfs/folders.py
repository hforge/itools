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
from __future__ import with_statement
from subprocess import call

# Import from itools
from itools.uri import uri
from registry import get_file_system



def get_fs_and_reference(base, reference):
    reference = base.resolve2(reference)
    fs = get_file_system(reference.scheme)
    return fs, reference



class Folder(object):

    __slots__ = ['uri']


    def __init__(self, uri=None):
        self.uri = uri


    def get_fs_and_reference(self, reference):
        """
        Internal function, from the given reference (usually a byte string),
        builds the absolute URI reference. Then find outs which is the
        protocol handler for it (layer), and returns both.
        """
        reference = uri.get_absolute_reference2(reference, base=self.uri)
        fs = get_file_system(reference.scheme)
        return fs, reference


    def exists(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.exists(reference)


    def is_file(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.is_file(reference)


    def is_folder(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.is_folder(reference)


    def get_ctime(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.get_ctime(reference)


    def get_mtime(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.get_mtime(reference)


    def get_atime(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.get_atime(reference)


    def get_mimetype(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.get_mimetype(reference)


    def get_size(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.get_size(reference)


    def make_file(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.make_file(reference)


    def make_folder(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.make_folder(reference)


    def remove(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.remove(reference)


    def open(self, reference, mode=None):
        fs, reference = self.get_fs_and_reference(reference)
        if not fs.exists(reference):
            raise LookupError, str(reference)

        if fs.is_file(reference):
            return fs.open(reference, mode)
        elif fs.is_folder(reference):
            return Folder(reference)            

        raise OSError


    def copy(self, source, target):
        if self.is_file(source):
            self.make_file(target)
            with self.open(source) as source:
                with self.open(target) as target:
                    target.write(source.read())
        elif self.is_folder(source):
            source_fs, source_reference = self.get_fs_and_reference(source)
            target_fs, target_reference = self.get_fs_and_reference(target)
            if source_fs is target_fs:
                source_fs.copy(source_reference, target_reference)
            else:
                # XXX
                raise NotImplementedError
        else:
            raise OSError


    def move(self, source, target):
        source_fs, source_reference = self.get_fs_and_reference(source)
        target_fs, target_reference = self.get_fs_and_reference(target)

        if source_fs is target_fs:
            # Move within the same fs
            source_fs.move(source_reference, target_reference)
        else:
            # Move across different fss (copy and remove)
            self.copy(source_reference, target_reference)
            self.remove(source_reference)


    def get_names(self, reference='.'):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.get_names(reference)
