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

# Import from itools
from itools.uri import uri
from registry import get_file_system
from folders import Folder


# Constants
READ = 'r'
WRITE = 'w'


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


def open(reference, mode=None):
    return cwd.open(reference, mode)


def copy(source, target):
    return cwd.copy(source, target)


def move(source, target):
    return cwd.move(source, target)


##########################################################################
# Folders only
def get_names(reference):
    return cwd.get_names(reference)
