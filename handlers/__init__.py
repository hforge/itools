# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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
from archive import ZIPFile, TARFile, GzipFile, Bzip2File
from base import Handler
from config import ConfigFile
from file import File
from folder import Folder
from image import Image
from python import Python
from registry import register_handler_class, get_handler_class, get_handler
from text import TextFile, guess_encoding
from database import Database, SafeDatabase
from database import READY, TRANSACTION_PHASE1, TRANSACTION_PHASE2
from utils import checkid, merge_dics


__all__ = [
    # Abstract classes
    'Handler',
    # Handlers
    'ZIPFile',
    'TARFile',
    'GzipFile',
    'Bzip2File',
    'ConfigFile',
    'File',
    'Folder',
    'Image',
    'Python',
    'TextFile',
    # The database
    'Database',
    'SafeDatabase',
    'READY',
    'TRANSACTION_PHASE1',
    'TRANSACTION_PHASE2',
    # Registry
    'get_handler_class',
    'register_handler_class',
    'get_handler',
    # Some functions
    'checkid',
    'guess_encoding',
    'merge_dics',
    ]

