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

# Import from the Standard Library
from optparse import OptionParser
from os import getenv
from time import time

# Import from itools
import itools
from itools import vfs
from itools.handlers import get_handler
from itools.catalog import (make_catalog, Catalog, KeywordField, TextField,
                            vmsize)
import itools.xml


# These are the fields we index
fields = [KeywordField('path', is_indexed=False, is_stored=True),
          TextField('text')]



def index(parser, options, target):
    # Create the catalog
    catalog = getenv('ICATALOG_DIR')
    if catalog is None:
        print 'Error: The environment variable ICATALOG_DIR is missing'
        return

    # Create the catalog
    catalog = make_catalog(catalog, *fields)

    # Index
    i = j = 0
    t0 = time()
    m0 = vmsize()
    for ref in vfs.traverse(target):
        # We only index files
        if not vfs.is_file(ref):
            continue

        # Load the handler
        handler = get_handler(ref)

        # Build the indexes
        indexes = {}
        path = unicode(str(ref.path), 'utf-8', 'replace')
        indexes['path'] = path

        try:
            text = handler.to_text()
        except NotImplementedError:
            continue
        except:
            print '!', path
            j += 1
            continue
        indexes['text'] = text
        i += 1

        # Index
        print i, path
        catalog.index_document(indexes)
        # Save changes every 1000 documents
        if i % 1000 == 0:
            catalog.commit()

    catalog.commit()
    m1 = vmsize()
    t1 = time()
    print
    print '%d files indexed (%d failed)' % (i, j)
    print 'Time taken: %d seconds. Memory used: %d' % (t1-t0, m1-m0)



if __name__ == '__main__':
    # The command line parser
    usage = '%prog FOLDER'
    version = 'itools %s' % itools.__version__
    description = ('Index all the files within the given FOLDER, into the'
                   ' catalog defined by the environment variable'
                   ' ICATALOG_DIR.')
    parser = OptionParser(usage, version=version, description=description)

    options, args = parser.parse_args()
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    target = args[0]

    # Action!
    index(parser, options, target)

