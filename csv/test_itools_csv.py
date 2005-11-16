# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#                    2005 Piotr Macuk <piotr@macuk.pl>
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
from itools.resources import memory
from itools.resources import get_resource
import itools_csv
from itools.datatypes import Date, Integer, Unicode, URI
from datetime import date


TEST_DATA_1 = """python,http://python.org,52343,2003-10-23
ruby,http://ruby-lang.org,42352,2001-03-28"""

TEST_DATA_2 = 'one,two,three\nfour,five,six\nseven,eight,nine'



class CSVTestCase(TestCase):

    def test_unicode(self):
        data = '"Martin von Löwis","Marc André Lemburg","Guido van Rossum"\n'
        resource = memory.File(data)
        handler = itools_csv.CSV(resource)
        self.assertEqual(handler.get_rows(), [[u"Martin von Löwis",
                                               u"Marc André Lemburg",
                                               u"Guido van Rossum"]])


    def test_num_of_lines(self):
        resource = memory.File(TEST_DATA_2)
        handler = itools_csv.CSV(resource)
        self.assertEqual(len(handler.get_rows()), 3)


    def test_num_of_lines_with_last_new_line(self):
        data = TEST_DATA_2 + '\r\n'
        resource = memory.File(data)
        handler = itools_csv.CSV(resource)
        self.assertEqual(len(handler.get_rows()), 3)

    
    def test_load_state_with_schema(self):
        resource = memory.File(TEST_DATA_1)
        handler = itools_csv.CSV()
        handler.columns = ['name', 'url', 'number', 'date']
        handler.schema = {'name': Unicode, 'url': URI, 'number': Integer,
                          'date': Date}
        handler.load_state(resource)
        self.assertEqual(handler.get_rows(), [
            [u"python", URI.decode('http://python.org'), 52343,
             Date.decode('2003-10-23')], 
            [u"ruby", URI.decode('http://ruby-lang.org'), 42352,
             Date.decode('2001-03-28')]])


    def test_load_state_without_schema(self):
        resource = memory.File(TEST_DATA_1)
        handler = itools_csv.CSV()
        handler.schema = {'name': Unicode, 'url': URI, 'number': Integer,
                          'date': Date}
        handler.load_state(resource)
        self.assertEqual(handler.get_rows(), [
            [u"python", u'http://python.org', u'52343', u'2003-10-23'], 
            [u"ruby", u'http://ruby-lang.org', u'42352', u'2001-03-28']])


    def test_to_str_with_schema(self):
        resource = memory.File(TEST_DATA_1)
        handler = itools_csv.CSV()
        handler.columns = ['name', 'url', 'number', 'date']
        handler.schema = {'name': Unicode, 'url': URI, 'number': Integer,
                          'date': Date}
        handler.load_state(resource)
        self.assertEqual(
            handler.to_str(),
            u'"python","http://python.org","52343","2003-10-23"\n'
            u'"ruby","http://ruby-lang.org","42352","2001-03-28"')


    def test_to_str_without_schema(self):
        resource = memory.File(TEST_DATA_1)
        handler = itools_csv.CSV()
        handler.load_state(resource)
        self.assertEqual(
            handler.to_str(),
            u'"python","http://python.org","52343","2003-10-23"\n'
            u'"ruby","http://ruby-lang.org","42352","2001-03-28"')


    def test_get_row(self):
        resource = memory.File(TEST_DATA_2)
        handler = itools_csv.CSV(resource)
        self.assertEqual(handler.get_row(1), ['four', 'five', 'six'])


    def test_get_rows(self):
        resource = memory.File(TEST_DATA_2)
        handler = itools_csv.CSV(resource)
        self.assertEqual(handler.get_rows([0, 1]), [
            ['one', 'two', 'three'], 
            ['four', 'five', 'six']])


    def test_add_row(self):
        resource = memory.File(TEST_DATA_2)
        handler = itools_csv.CSV(resource)
        handler.add_row(['a', 'b', 'c'])
        self.assertEqual(handler.get_row(3), ['a', 'b', 'c'])


    def test_del_row(self):
        resource = memory.File(TEST_DATA_2)
        handler = itools_csv.CSV(resource)
        handler.del_row(1)
        self.assertEqual(handler.get_row(1), ['seven', 'eight', 'nine'])


    def test_del_rows(self):
        resource = memory.File(TEST_DATA_2)
        handler = itools_csv.CSV(resource)
        handler.del_rows([0, 1])
        self.assertEqual(handler.get_row(0), ['seven', 'eight', 'nine'])


    def test_set_state_in_memory_resource(self):
        resource = memory.File(TEST_DATA_2)
        handler = itools_csv.CSV(resource)
        handler.add_row(['a', 'b', 'c'])
        handler.save_state()
        handler2 = itools_csv.CSV(resource)
        self.assertEqual(handler2.get_row(3), ['a', 'b', 'c'])


    def test_set_state_in_file_resource(self):
        resource = get_resource('test.csv')
        handler = itools_csv.CSV(resource)
        handler.add_row(['d1', 'e1', 'f1'])
        handler.save_state()

        resource2 = get_resource('test.csv')
        handler2 = itools_csv.CSV(resource2)
        self.assertEqual(handler2.get_row(3), ['d1', 'e1', 'f1'])
        handler2.del_row(3)
        handler2.save_state()


    def test_indexes_hit_in_one_row(self):
        data = TEST_DATA_1
        resource = memory.File(data)
        handler = itools_csv.CSV()
        handler.columns = ['name', 'url', 'number', 'date']
        handler.schema = {'name': Unicode, 'url': URI,
                          'number': Integer(index=True),
                          'date': Date(index=True)}
        handler.load_state(resource)
        self.assertEqual(len(handler.state.indexes), 4)
        self.assertEqual(
            handler.search([('url', URI.decode('http://slashdot.org/'))]),None)
        self.assertEqual(handler.search([('number', 52343)]), [0])
        self.assertEqual(
            handler.search([('date', Date.decode('2001-03-28'))]), [1])
    

    def test_indexes_hit_in_many_rows(self):
        data = 'house,2005-10-10\nwindow,2005-05-10\ncomputer,2005-10-10'
        resource = memory.File(data)
        handler = itools_csv.CSV()
        handler.columns = ['name', 'date']
        handler.schema = {'name': Unicode, 'date': Date(index=True)}
        handler.load_state(resource)
        self.assertEqual(
            handler.search([('name', Unicode.decode('house'))]), None)
        self.assertEqual(
            handler.search([('date', Date.decode('2005-01-01'))]), [])
        self.assertEqual(
            handler.search([('date', Date.decode('2005-10-10'))]), [0, 2])


    def test_index_new_row(self):
        data = 'house,2005-10-10\nwindow,2005-05-10\ncomputer,2005-10-10'
        resource = memory.File(data)
        handler = itools_csv.CSV()
        handler.columns = ['name', 'date']
        handler.schema = {'name': Unicode, 'date': Date(index=True)}
        handler.load_state(resource)
        handler.add_row(['flower', Date.decode('2005-05-10')])
        self.assertEqual(
            handler.search([('date', Date.decode('2005-05-10'))]), [1, 3])


    def test_index_del_row(self):
        data = 'house,2005-10-10\nwindow,2005-05-10\ncomputer,2005-10-10'
        resource = memory.File(data)
        handler = itools_csv.CSV()
        handler.columns = ['name', 'date']
        handler.schema = {'name': Unicode(index=True),
                          'date': Date(index=True)}
        handler.load_state(resource)
        self.assertEqual(handler.search([('name', 'window')]), [1])
        handler.del_row(1)
        self.assertEqual(handler.search([('name', 'window')]), [])
        
        self.assertEqual(handler.search([('name', 'computer')]), [1])
        handler.del_row(1)
        self.assertEqual(handler.search([('name', 'computer')]), [])
        

    def test_build_csv_data(self):
        resource = memory.File('')
        handler = itools_csv.CSV()
        handler.columns = ['name', 'surname', 'date']
        handler.schema = {'name': Unicode, 'surname': Unicode(index=True),
                          'date': Date(index=True)}
        handler.load_state(resource)
        handler.add_row(['Piotr', 'Macuk', '1975-12-08'])
        handler.add_row(['Basia', 'Macuk', '2002-02-14'])
        self.assertEqual(handler.search([('surname', 'Macuk')]), [0, 1])
        handler.add_row(['Pawe³', 'Macuk', '1977-05-13'])
        self.assertEqual(handler.search([('surname', 'Macuk')]), [0, 1, 2])
        handler.del_row(2)
        self.assertEqual(handler.search([('surname', 'Macuk')]), [0, 1])
        handler.del_row(0)
        self.assertEqual(handler.search([('surname', 'Macuk')]), [0])


    def test_and_operator(self):
        left = [0, 1, 3, 5, 6, 8]
        right = [1, 2, 3, 9]
        handler = itools_csv.CSV()
        self.assertEqual(handler._and(left, right), [1, 3])


    def test_and_operator2(self):
        left = [0, 1, 3, 5, 6, 8]
        right = []
        handler = itools_csv.CSV()
        self.assertEqual(handler._and(left, right), [])


    def test_or_operator(self):
        left = [0, 1, 3, 5, 6, 8]
        right = [1, 2, 3, 9]
        handler = itools_csv.CSV()
        self.assertEqual(handler._or(left, right), [0, 1, 2, 3, 5, 6, 8, 9])


    def test_or_operator2(self):
        left = []
        right = [1, 2]
        handler = itools_csv.CSV()
        self.assertEqual(handler._or(left, right), [1, 2])


    def test_advanced_search(self):
        resource = get_resource('test_adv.csv')
        handler = itools_csv.CSV()
        handler.columns = ['id', 'name', 'country', 'date']
        handler.schema = {'id': Integer, 'name': Unicode(index=True),
                          'country': Unicode(index=True),
                          'date': Date(index=True)}
        handler.load_state(resource)
        result1 = handler.search([
            ('name', 'dde'), 'and', ('country', 'Sweden')
        ])
        self.assertEqual(result1, [5, 6])

        result2 = handler.search([
            ('name', 'dde'), 
            'or', 
            ('name', 'fse'),
            'and',
            ('country', 'France')
        ])
        self.assertEqual(result2, [4])

        # previous results as query items
        result3 = handler.search([
            ('name', 'dde'), 'or', ('name', 'fse'),
        ])
        result4 = handler.search([
            ('country', 'Poland'), 'or', ('country', 'France'),
        ])
        result5 = handler.search([result3, 'and', result4])
        self.assertEqual(result5, [1, 4])

        # id is not indexed -- return None
        result6 = handler.search([
            ('id', 3), 'or', ('country', 'Poland')
        ])
        self.assertEqual(result6, None)



if __name__ == '__main__':
    unittest.main()
