# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools
from itools.handlers import get_handler
from itools.handlers.Text import Text
from Catalog import Catalog
from IIndex import IIndex


class IITestCase(TestCase):

    def test_hit(self):
        ii = IIndex()
        ii.index_term(u'hello', 0, 0)
        assert bool(ii.search_word(u'hello')) is True


    def test_miss(self):
        ii = IIndex()
        ii.index_term(u'hello', 0, 0)
        assert bool(ii.search_word(u'bye')) is False


    def test_unindex(self):
        ii = IIndex()
        ii.index_term(u'hello', 0, 0)
        ii.unindex_term(u'hello', 0)
        assert bool(ii.search_word(u'hello')) is False



class Document(Text):

    def _load_state(self, resource):
        # Pre-process (load as unicode)
        Text._load_state(self, resource)
        state = self.state
        data = state.data
        del state.data
        # Extract the title and body
        lines = data.split('\n')
        state.title = lines[0]
        state.body = '\n'.join(lines[3:])


    def title(self):
        return self.state.title


    def body(self):
        return self.state.body




# Build a catalog on memory
tests = get_handler('tests')
if tests.has_handler('catalog'):
    tests.del_handler('catalog')
catalog = Catalog(fields=[('title', 'text', True, True),
                          ('body', 'text', True, False)])
tests.set_handler('catalog', catalog)
tests.save_state()
catalog_resource = tests.resource.get_resource('catalog')
catalog = Catalog(catalog_resource)

resource_names = [ x for x in tests.get_handler_names()
                   if x.endswith('.txt') ]
resource_names.sort()
for resource_name in resource_names:
    resource = tests.resource.get_resource(resource_name)
    document = Document(resource)
    catalog.index_document(document)
catalog.save_state()



class CatalogTestCase(TestCase):

    def test_hit(self):
        documents = catalog.search(body='forget')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [5, 10])


    def test_phrase(self):
        documents = catalog.search(body='your son')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [5])


    def test_miss(self):
        documents = catalog.search(body='plano')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [])


    def test_unindex(self):
        catalog.unindex_document(5)
        documents = catalog.search(body='forget')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [10])


##    def test_save(self):
##        if tests.has_resource('catalog'):
##            tests.del_resource('catalog')
##        tests.set_handler('catalog', catalog)
##        catalog_resource = tests.get_resource('catalog')
##        fs_catalog = Catalog.Catalog(catalog_resource)

##        documents = catalog.search(body='forget')
##        doc_numbers = [ x.__number__ for x in documents ]
##        self.assertEqual(doc_numbers, [5, 10])

##        documents = catalog.search(body='plano')
##        doc_numbers = [ x.__number__ for x in documents ]
##        self.assertEqual(doc_numbers, [])



if __name__ == '__main__':
    unittest.main()
