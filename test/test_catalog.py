# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.handlers.spaces import get_space
from itools.handlers import get_handler
from itools.handlers.Text import Text
from itools.catalog import IO
from itools.catalog import analysers
from itools.catalog.index import Index
from itools.catalog.catalog import Catalog
from itools.catalog.documents import Document, Documents
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



class AnalysersTestCase(TestCase):

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



class IndexTestCase(TestCase):

    def test00_new(self):
        index = Index()
        # Index "hello world"
        index.index_term(u'hello', 0, 0)
        index.index_term(u'world', 0, 1)
        # Save
        index.save_state_to('tests/index')


    def test01_load_and_search(self):
        index = Index('tests/index')
        self.assertEqual(index.search_word(u'heelo'), {})
        self.assertEqual(index.search_word(u'hello'), {0: [0]})
        self.assertEqual(index.search_word(u'world'), {0: [1]})


    def test02_unindex(self):
        index = Index('tests/index')
        index.unindex_term(u'hello', 0)
        index.save_state()


    def test03_load_and_search(self):
        index = Index('tests/index')
        self.assertEqual(index.search_word(u'hello'), {})
        self.assertEqual(index.search_word(u'world'), {0: [1]})


    def test04_search_range(self):
        index = Index('tests/index')
        # Index data
        index.index_term(u'1975-05-28', 1, 0)
        index.index_term(u'2003-03-03', 2, 0)
        index.index_term(u'2006-07-08', 3, 0)
        index.index_term(u'2006-07-09', 4, 0)
        index.save_state()
        # Test search
        self.assertEqual(index.search_range(u'2003-03-03', u'2006-07-09'),
                         {2: 1, 3: 1})
        self.assertEqual(index.search_range(u'', u'2006-07-09'),
                         {1: 1, 2: 1, 3: 1})
        self.assertEqual(index.search_range(u'2003-03-03', u'6666-12-31'),
                         {2: 1, 3: 1, 4: 1})



class DocumentsTestCase(TestCase):

    def test00_new(self):
        documents = Documents()
        # Index document
        document = Document(u'hello world')
        doc_n = documents.index_document(document)
        self.assertEqual(doc_n, 0)
        # Another document
        document = Document(u'bye world')
        doc_n = documents.index_document(document)
        self.assertEqual(doc_n, 1)
        # Save
        documents.save_state_to('tests/documents')


    def test01_load_and_search(self):
        documents = Documents('tests/documents')
        # Document 0
        document = documents.get_document(0)
        self.assertEqual(document.fields[0], u'hello world')
        # Document 1
        document = documents.get_document(1)
        self.assertEqual(document.fields[0], u'bye world')


    def test02_unindex(self):
        documents = Documents('tests/documents')
        documents.unindex_document(0)
        documents.save_state()


    def test03_load_and_search(self):
        documents = Documents('tests/documents')
        # Document 0
        self.assertRaises(LookupError, documents.get_document, 0)
        # Document 1
        document = documents.get_document(1)
        self.assertEqual(document.fields[0], u'bye world')



class CatalogTestCase(TestCase):
    
    def test00_new(self):
        catalog = Catalog(fields=[('body', 'text', True, True)])
        # Index "hello world"
        catalog.index_document({'body': u'hello world'})
        catalog.index_document({'body': u'bye world'})
        # Save
        catalog.save_state_to('tests/catalog')


    def test01_load_and_search(self):
        catalog = Catalog('tests/catalog')
        # Search "hello"
        results = list(catalog.search(body=u'hello'))
        self.assertEqual(len(results), 1)
        # Search "world"
        results = list(catalog.search(body=u'world'))
        self.assertEqual(len(results), 2)
        # Search "moon"
        results = list(catalog.search(body=u'moon'))
        self.assertEqual(len(results), 0)


    def test02_unindex(self):
        catalog = Catalog('tests/catalog')
        catalog.unindex_document(0)
        catalog.save_state()


    def test03_load_and_search(self):
        catalog = Catalog('tests/catalog')
        # Search "hello"
        results = list(catalog.search(body=u'hello'))
        self.assertEqual(len(results), 0)
        # Search "world"
        results = list(catalog.search(body=u'world'))
        self.assertEqual(len(results), 1)








#class Document(Text):

#    def _load_state_from_file(self, file):
#        # Pre-process (load as unicode)
#        Text._load_state_from_file(self, file)
#        data = self.data
#        del self.data
#        # Extract the title and body
#        lines = data.split('\n')
#        self.title = lines[0]
#        self.body = '\n'.join(lines[3:])


#    def title(self):
#        return self.title


#    def body(self):
#        return self.body




# Build a catalog on memory
#tests = get_handler('fables')
#if tests.has_handler('catalog'):
#    tests.del_handler('catalog')
#catalog = Catalog(fields=[('title', 'text', True, True),
#                          ('body', 'text', True, False)])
#tests.set_handler('catalog', catalog)
#tests.save_state()
#catalog_resource = tests.resource.get_resource('catalog')
#catalog = Catalog(catalog_resource)
#
#resource_names = [ x for x in tests.get_handler_names() if x.endswith('.txt') ]
#resource_names.sort()
#for resource_name in resource_names:
#    resource = tests.resource.get_resource(resource_name)
#    document = Document(resource)
#    document = {'title': document.title, 'body': document.body}
#    catalog.index_document(document)
#catalog.save_state()



#class CatalogTestCase(TestCase):

#    def test_hit(self):
#        documents = catalog.search(body='forget')
#        doc_numbers = [ x.__number__ for x in documents ]
#        self.assertEqual(doc_numbers, [5, 10])


#    def test_phrase(self):
#        documents = catalog.search(body='your son')
#        doc_numbers = [ x.__number__ for x in documents ]
#        self.assertEqual(doc_numbers, [5])


#    def test_miss(self):
#        documents = catalog.search(body='plano')
#        doc_numbers = [ x.__number__ for x in documents ]
#        self.assertEqual(doc_numbers, [])


#    def test_range(self):
#        query = queries.Range('body', 'home', 'horse')
#        documents = catalog.search(query)
#        doc_numbers = [ x.__number__ for x in documents ]
#        self.assertEqual(doc_numbers,
#                         [22, 17, 2, 30, 25, 19, 16, 13, 12, 11, 8, 5])


#    def test_unindex(self):
#        catalog.unindex_document(5)
#        documents = catalog.search(body='forget')
#        doc_numbers = [ x.__number__ for x in documents ]
#        self.assertEqual(doc_numbers, [10])


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
