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


# Import from Python
import unittest
from unittest import TestCase

# Import from itools
from itools.handlers import get_handler, Text
import Index
import Lucene
import Segment



class EncodeDecodeTestCase(TestCase):
    """
    This test case is to test the encoders/decoders, which are implemented
    in the Lucene.File class.
    """

    def setUp(self):
        self.file = Lucene.File()


    def init(self, data):
        self.file.data = data
        self.file.index = 0


    def test_byte(self):
        for x in range(256):
            byte = self.file.save_byte(x)
            self.init(byte)
            y = self.file.load_byte()
            self.assertEqual(x, y)


    def test_int32(self):
        limit = 2**16
        for x in range(-limit, limit, 64):
            int32 = self.file.save_int32(x)
            self.init(int32)
            y = self.file.load_int32()
            self.assertEqual(x, y)


    def test_uint32(self):
        for x in range(0, 2**16, 64):
            uint32 = self.file.save_uint32(x)
            self.init(uint32)
            y = self.file.load_uint32()
            self.assertEqual(x, y)


    def test_uint64(self):
        for x in range(0, 2**16, 128):
            uint64 = self.file.save_uint64(x)
            self.init(uint64)
            y = self.file.load_uint64()
            self.assertEqual(x, y)


    def test_vint(self):
        for x in range(0, 32768, 7):
            vint = self.file.save_vint(x)
            self.init(vint)
            y = self.file.load_vint()
            self.assertEqual(x, y)


    def test_string(self):
        x = 'toto'
        string = self.file.save_string(x)
        self.init(string)
        y = self.file.load_string()
        self.assertEqual(x, y)



class AnalyserTestCase(TestCase):
    def test_analyser(self):
        text = "Inferno is meant to be a better Plan 9, which was meant to" \
               " be a better Unix."
        analyser = Segment.Analyser(text)
        words = []
        word, position = analyser.next_word()
        while word is not None:
            words.append((word, position))
            word, position = analyser.next_word()
        self.assertEqual([(u'inferno', 0), (u'meant', 1), (u'better', 2),
                          (u'plan', 3), (u'meant', 4), (u'better', 5),
                          (u'unix', 6)], words)



class Document(Text.Text):
    def _load(self, resource):
        data = resource.get_data()
        lines = data.split('\n')
        self.title = lines[0]
        self.body = '\n'.join(lines[3:])



# Build an index on memory
index = Index.Index(fields=[('title', True, True), ('body', True, False)])

tests = get_handler('tests')
resource_names = [ x for x in tests.get_resources() if x.endswith('.txt') ]
resource_names.sort()
for resource_name in resource_names:
    resource = tests.get_resource(resource_name)
    document = Document(resource)
    index.index_document(document)


class IndexTestCase(TestCase):
    def test_hit(self):
        documents = index.search(body='forget')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [5, 10])


    def test_miss(self):
        documents = index.search(body='plano')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [])


    def test_unindex(self):
        index.unindex_document(5)
        documents = index.search(body='forget')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [10])


    def test_save(self):
        if tests.has_resource('index'):
            tests.del_resource('index')
        tests.set_handler('index', index)
        index_resource = tests.get_resource('index')
        fs_index = Index.Index(index_resource)

        documents = index.search(body='forget')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [5, 10])

        documents = index.search(body='plano')
        doc_numbers = [ x.__number__ for x in documents ]
        self.assertEqual(doc_numbers, [])



if __name__ == '__main__':
    unittest.main()
