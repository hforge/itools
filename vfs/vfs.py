# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2009 David Versmisse <david.versmisse@itaapy.com>
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

# Import from itools
from folder import Folder, READ


cwd = Folder()


def exists(reference):
    return cwd.exists(reference)


def is_file(reference):
    return cwd.is_file(reference)


def is_folder(reference):
    return cwd.is_folder(reference)


def can_read(reference):
    return cwd.can_read(reference)


def can_write(reference):
    return cwd.can_write(reference)


def get_ctime(reference):
    return cwd.get_ctime(reference)


def get_mtime(reference):
    return cwd.get_mtime(reference)


def get_atime(reference):
    return cwd.get_atime(reference)


def get_mimetype(reference):
    return cwd.get_mimetype(reference)


def get_size(reference):
    return cwd.get_size(reference)


def make_file(reference):
    return cwd.make_file(reference)


def make_folder(reference):
    return cwd.make_folder(reference)


def remove(reference):
    return cwd.remove(reference)


def open(reference, mode=READ):
    return cwd.open(reference, mode)


def copy(source, target):
    return cwd.copy(source, target)


def move(source, target):
    return cwd.move(source, target)


def get_names(reference):
    return cwd.get_names(reference)


def traverse(reference):
    return cwd.traverse(reference)


def mount_archive(reference):
    return cwd.mount_archive(reference)
