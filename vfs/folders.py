# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from __future__ import with_statement

# Import from itools
from itools.uri import get_absolute_reference2
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
        reference = get_absolute_reference2(reference, base=self.uri)
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


    def can_read(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.can_read(reference)


    def can_write(self, reference):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.can_write(reference)


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

        raise OSError, str(reference)


    def copy(self, source, target):
        source_fs, source_ref = self.get_fs_and_reference(source)
        target_fs, target_ref = self.get_fs_and_reference(target)
        # If the target exists and is a folder, copy the source within it
        if target_fs.is_folder(target_ref):
            target_ref = target_ref.resolve2(source_ref.path[-1])

        # File
        if source_fs.is_file(source_ref):
            target_fs.make_file(target_ref)
            with source_fs.open(source_ref) as source:
                with target_fs.open(target_ref, 'w') as target:
                    target.write(source.read())
            return

        # Folder
        if source_fs.is_folder(source_ref):
            source_root = source_ref
            target_root = target_ref
            for source_ref in source_fs.traverse(source_root):
                offset = source_root.path.get_pathto(source_ref.path)
                target_ref = target_root.resolve2(offset)
                if source_fs.is_folder(source_ref):
                    target_fs.make_folder(target_ref)
                else:
                    with source_fs.open(source_ref, 'r') as file:
                        data = file.read()
                    with target_fs.make_file(target_ref) as file:
                        file.write(data)
            return

        # Something else
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


    def traverse(self, reference='.'):
        fs, reference = self.get_fs_and_reference(reference)
        return fs.traverse(reference)
