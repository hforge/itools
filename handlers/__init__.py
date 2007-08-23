# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from the Standard Library
import mimetypes

# Import from itools
from archive import ZipArchive, TarArchive, Gzip, Bzip2
from base import Node, Handler
from config import Config
from exceptions import AcquisitionError
from file import File
from folder import Folder
from image import Image
from python import Python
from registry import get_handler_class, register_handler_class
from text import Text
from database import Database, READY, TRANSACTION_PHASE1, TRANSACTION_PHASE2
from utils import get_handler
from table import Table, parse_table, fold_line, escape_data


__all__ = [
    # Exceptions
    'AcquisitionError',
    # Abstract classes
    'Node',
    'Handler',
    # Handlers
    'ZipArchive',
    'TarArchive',
    'Gzip',
    'Bzip2',
    'Config',
    'File',
    'Folder',
    'Image',
    'Python',
    'Text',
    'Table',
    # The database
    'Database',
    'READY',
    'TRANSACTION_PHASE1',
    'TRANSACTION_PHASE2',
    # Parsing functions
    'parse_table',
    'fold_line',
    'escape_data',
    # Registry
    'get_handler_class',
    'register_handler_class',
    # Other functions
    'get_handler']



mimetypes.add_type('text/comma-separated-values', '.csv')
mimetypes.encodings_map['.bz2'] = 'bzip2'
