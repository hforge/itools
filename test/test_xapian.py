# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007-2008 Henry Obein <henry@itaapy.com>
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
from datetime import date
from random import sample
import unittest
from unittest import TestCase

# Import from itools
from itools import vfs
from itools.catalog import (CatalogAware, BoolField, KeywordField, TextField,
                            IntegerField, RangeQuery, EqQuery, NotQuery)
from itools.xapian import make_catalog, Catalog


class CatalogTestCase(TestCase):

    def setUp(self):
        # Make the catalog
        catalog = make_catalog('tests/catalog')
        # Index
        fables = vfs.open('fables')
        for name in fables.get_names():
            uri = fables.uri.resolve2(name)
            document = Document(uri)
            catalog.index_document(document)
        # Save
        catalog.save_changes()


    def tearDown(self):
        vfs.remove('tests/catalog')

    def test_everything(self):
        catalog = Catalog('tests/catalog')
        # Simple Search, hit
        results = catalog.search(data=u'lion')
        self.assertEqual(results.get_n_documents(), 4)
        documents = [ x.name for x in results.get_documents(sort_by='name') ]
        # XXX not yet implemented :-(
        #self.assertEqual(documents, ['03.txt', '08.txt', '10.txt', '23.txt'])

        # Simple Search, miss
        self.assertEqual(catalog.search(data=u'tiger').get_n_documents(), 0)
        # Unindex, Search, Abort, Search
        catalog.unindex_document('03.txt')
        results = catalog.search(data=u'lion')
        self.assertEqual(catalog.search(data=u'lion').get_n_documents(), 3)
        catalog.abort_changes()
        self.assertEqual(catalog.search(data=u'lion').get_n_documents(), 4)
        # Phrase Query
        results = catalog.search(data=u'this is a double death')
        self.assertEqual(results.get_n_documents(), 1)

        # Range Query
        # XXX not yet implemented
        #query = RangeQuery('data', 'home', 'horse')
        #results = catalog.search(query)
        #self.assertEqual(results.get_n_documents(), 12)

        # Not Query
        query = NotQuery(EqQuery('data', 'lion'))
        results = catalog.search(query)
        self.assertEqual(results.get_n_documents(), 27)


    def test_unique_values(self):
        catalog = Catalog('tests/catalog')
        values = catalog.get_unique_values('title')
        self.assert_('pearl' in values)
        self.assert_('motorola' not in values)



class Document(CatalogAware):

    def __init__(self, uri):
        self.uri = uri


    def get_catalog_fields(self):
        return [
            KeywordField('name', is_stored=True),
            # XXX title should not be indexed!
            TextField('title', is_indexed=True, is_stored=True),
            TextField('data'),
            IntegerField('size')]


    def get_catalog_values(self):
        data = vfs.open(self.uri).read()

        indexes = {}
        indexes['name'] = self.uri.path[-1]
        indexes['title'] = data.splitlines()[0]
        indexes['data'] = data
        indexes['size'] = len(data)
        return indexes



if __name__ == '__main__':
    unittest.main()
