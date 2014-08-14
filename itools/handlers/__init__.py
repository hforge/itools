# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007-2008 Hervé Cauwelier <herve@oursours.net>
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

"""
This package provides an abstraction layer for files and directories.
There are two key concepts, resources and handlers.

A resource is anything that behaves like a file (it contains an array of
bytes), as a directory (it contains other resources) or as a link (it
contains a path or an uri to another resource). Doesn't matters wether
a resource lives in the local file system, in a database or is a remote
object accessed with an URI.

A resource handler adds specific semantics to different resources, for
example there is a handler to manage XML files, another to manage PO
files, etc...
"""

# Import from itools
from archive import ZIPFile, TARFile, GzipFile, Bzip2File, TGZFile, TBZ2File
from base import Handler
from config import ConfigFile
from file import File
from folder import Folder
from image import Image, SVGFile
from js import JSFile
from registry import register_handler_class, get_handler_class_by_mimetype
from text import TextFile, guess_encoding
from database import RODatabase
from database import ro_database
from utils import checkid


__all__ = [
    # Abstract classes
    'Handler',
    # Handlers
    'ConfigFile',
    'File',
    'Folder',
    'Image',
    'SVGFile',
    'JSFile',
    'TextFile',
    # Handlers / Archive
    'ZIPFile',
    'TARFile',
    'GzipFile',
    'Bzip2File',
    'TGZFile',
    'TBZ2File',
    # The database
    'RODatabase',
    'ro_database',
    # Registry
    'get_handler_class_by_mimetype',
    'register_handler_class',
    # Some functions
    'checkid',
    'guess_encoding',
    ]

