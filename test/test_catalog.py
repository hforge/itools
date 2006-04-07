# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools
from itools.handlers import get_handler
from itools.handlers.Text import Text
from itools.catalog import IO
from itools.catalog import analysers
from itools.catalog.Catalog import Catalog
from itools.catalog.IIndex import IIndex
from itools.catalog import queries



class IOTestCase(TestCase):

    def test_byte(self):
        value = 27
        encoded_value = IO.encode_byte(value)
        self.assertEqual(IO.decode_byte(encoded_value), value)


    def test_unit32(self):
        value = 1234
        encoded_value = IO.encode_uint32(value)
        self.assertEqual(IO.decode_uint32(encoded_value), value)


    def test_vint(self):
        value = 1234567890
        encoded_value = IO.encode_vint(value)
        self.assertEqual(IO.decode_vint(encoded_value)[0], value)


    def test_character(self):
        value = u'X'
        encoded_value = IO.encode_character(value)
        self.assertEqual(IO.decode_character(encoded_value), value)


    def test_string(self):
        value = u'aquilas non captis muscas'
        encoded_value = IO.encode_string(value)
        self.assertEqual(IO.decode_string(encoded_value)[0], value)


    def test_link(self):
        for value in [0, 513]:
            encoded_value = IO.encode_link(value)
            self.assertEqual(IO.decode_link(encoded_value), value)


    def test_version(self):
        value = '20050217'
        encoded_value = IO.encode_version(value)
        self.assertEqual(IO.decode_version(encoded_value), value)



class TextTestCase(TestCase):

    def test_hello(self):
        words = list(analysers.Text(u'Hello world'))
        self.assertEqual(words, [(u'hello', 0), (u'world', 1)])


    def test_accents(self):
        words = list(analysers.Text(u'Te doy una canción'))
        self.assertEqual(words, [(u'te', 0), (u'doy', 1), (u'una', 2),
                                 (u'canción', 3)])


    def test_russian(self):
        text = u'Это наш дом'
        words = list(analysers.Text(text))
        self.assertEqual(words, [(u'это', 0), (u'наш', 1),  (u'дом', 2)])



class IITestCase(TestCase):

    def test_hit(self):
        ii = IIndex()
        ii.index_term(u'hello', 0, 0)
        self.assertEqual(bool(ii.search_word(u'hello')), True)


    def test_miss(self):
        ii = IIndex()
        ii.index_term(u'hello', 0, 0)
        self.assertEqual(bool(ii.search_word(u'bye')), False)


    def test_unindex(self):
        ii = IIndex()
        ii.index_term(u'hello', 0, 0)
        ii.unindex_term(u'hello', 0)
        self.assertEqual(bool(ii.search_word(u'hello')), False)



class Document(Text):

    def _load_state(self, resource):
        # Pre-process (load as unicode)
        Text._load_state(self, resource)
        data = self.data
        del self.data
        # Extract the title and body
        lines = data.split('\n')
        self.title = lines[0]
        self.body = '\n'.join(lines[3:])


    def title(self):
        return self.title


    def body(self):
        return self.body




# Build a catalog on memory
tests = get_handler('fables')
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
    document = {'title': document.title, 'body': document.body}
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


    def test_range(self):
        query = queries.Range('body', 'home', 'horse')
        documents = catalog.search(query)
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers,
                         [22, 17, 2, 30, 25, 19, 16, 13, 12, 11, 8, 5])


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
