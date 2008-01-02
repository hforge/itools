# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from itools.catalog import (make_catalog, Catalog, CatalogAware, BoolField,
    KeywordField, TextField, IntegerField, RangeQuery, EqQuery, NotQuery)
from itools.catalog import io



class IOTestCase(TestCase):

    def test_byte(self):
        for value in range(255):
            aux = io.encode_byte(value)
            aux = io.decode_byte(aux)
            self.assertEqual(aux, value)


    def test_unit32(self):
        for value in sample(xrange(2**30), 255):
            aux = io.encode_uint32(value)
            aux = io.decode_uint32(aux)
            self.assertEqual(aux, value)


    def test_vint(self):
        for value in sample(xrange(2**30), 255):
            aux = io.encode_vint(value)
            aux = io.decode_vint(aux)
            self.assertEqual(aux[0], value)


    def test_character(self):
        for value in u"L'inégalité parmi les hommes":
            aux = io.encode_character(value)
            aux = io.decode_character(aux)
            self.assertEqual(aux, value)


    def test_string(self):
        for value in [u"L'inégalité parmi les hommes",
                      u'Aquilas non captis muscas']:
            aux = io.encode_string(value)
            aux = io.decode_string(aux)
            self.assertEqual(aux[0], value)


    def test_link(self):
        for value in sample(xrange(2**30), 255):
            aux = io.encode_link(value)
            aux = io.decode_link(aux)
            self.assertEqual(aux, value)
        # NULL
        aux = io.encode_link(None)
        aux = io.decode_link(aux)
        self.assertEqual(aux, None)


    def test_version(self):
        today = date.today()
        today = today.strftime('%Y%m%d')
        for value in [Catalog.class_version, today]:
            aux = io.encode_version(value)
            aux = io.decode_version(aux)
            self.assertEqual(aux, value)



class FieldsTestCase(TestCase):

    def test_boolean_true(self):
        words = list(BoolField.split(True))
        self.assertEqual(words, [(u'1', 0)])


    def test_boolean_false(self):
        words = list(BoolField.split(False))
        self.assertEqual(words, [(u'0', 0)])


    def test_keyword(self):
        value = 'Hello World'
        words = list(KeywordField.split(value))

        self.assertEqual(words, [(u'Hello World', 0)])


    def test_integer(self):
        for value in sample(xrange(1000000000), 255):
            words = list(IntegerField.split(value))
            self.assertEqual(len(words), 1)
            word, position = words[0]
            self.assertEqual(position, 0)
            self.assertEqual(type(word), unicode)
            self.assertEqual(int(word), value)


    def test_text(self):
        value = (u'Celle-ci consiste dans les differents Privileges, dont'
                 u' quelques-uns jouissent, au préjudice des autres,')
        expected = [u'celle', u'ci', u'consiste', u'dans', u'les',
            u'differents', u'privileges', u'dont', u'quelques', u'uns',
            u'jouissent', u'au', u'préjudice', u'des', u'autres']

        words = list(TextField.split(value))
        expected = [ (y, x) for x, y in enumerate(expected) ]
        self.assertEqual(words, expected)


    def test_text_russian(self):
        text = u'Это наш дом'
        words = list(TextField.split(text))
        self.assertEqual(words, [(u'это', 0), (u'наш', 1),  (u'дом', 2)])



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
        self.assertEqual(documents, ['03.txt', '08.txt', '10.txt', '23.txt'])
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
        query = RangeQuery('data', 'home', 'horse')
        results = catalog.search(query)
        self.assertEqual(results.get_n_documents(), 12)
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
            TextField('title', is_indexed=False, is_stored=True),
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
