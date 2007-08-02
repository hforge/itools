#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from optparse import OptionParser
from os import getenv

# Import from itools
import itools
from itools import vfs
from itools.catalog import make_catalog, Catalog, KeywordField, TextField
from itools.handlers import get_handler


def search(parser, options, args):
    text = args[0]

    # Create the catalog
    catalog = getenv('ICATALOG_DIR')
    if catalog is None:
        print 'Error: The environment variable ICATALOG_DIR is missing'
        return

    # Create the catalog
    catalog = Catalog(catalog)

    # Index
    results = catalog.search(text=text)
    for doc in results.get_documents():
        print doc.path



if __name__ == '__main__':
    # The command line parser
    usage = '%prog TEXT'
    version = 'itools %s' % itools.__version__
    description = ('Search the given TEXT in the catalog defined by the'
                   ' environment variable ICATALOG_DIR.')
    parser = OptionParser(usage, version=version, description=description)

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    # Action!
    search(parser, options, args)

