# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2005-2006 Piotr Macuk <piotr@macuk.pl>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.datatypes import Boolean, Date, Integer, Unicode, URI
from itools.catalog import AndQuery, OrQuery, EqQuery
from itools.csv import CSV


TEST_DATA_1 = """python,http://python.org/,52343,2003-10-23
ruby,http://ruby-lang.org/,42352,2001-03-28"""

TEST_DATA_2 = 'one,two,three\nfour,five,six\nseven,eight,nine'

TEST_SYNTAX_ERROR = '"one",,\n,"two",,\n,,"three"'



class Languages(CSV):
    __slots__ = CSV.__slots__
    columns = ['name', 'url', 'number', 'date']
    schema = {'name': Unicode,
              'url': URI,
              'number': Integer(index='keyword'),
              'date': Date(index='keyword')}


class Things(CSV):
    __slots__ = CSV.__slots__
    columns = ['name', 'date']
    schema = {'name': Unicode(index='text'), 'date': Date(index='keyword')}


class Numbers(CSV):
    __slots__ = CSV.__slots__
    columns = ['one', 'two', 'three']
    schema = {'one': Unicode, 'two': Unicode, 'three': Unicode}


class People(CSV):
    __slots__ = CSV.__slots__
    columns = ['name', 'surname', 'date']
    schema = {'name': Unicode,
              'surname': Unicode(index='text'),
              'date': Date(index='keyword')}


class Countries(CSV):
    __slots__ = CSV.__slots__
    columns = ['id', 'name', 'country', 'date']
    schema = {'id': Integer,
              'name': Unicode(index='text'),
              'country': Unicode(index='text'),
              'date': Date(index='keyword')}


class Politicians(CSV):
    __slots__ = CSV.__slots__
    columns = ['name', 'is_good']
    schema = {'name': Unicode, 'is_good': Boolean(index='bool')}




class CSVTestCase(TestCase):

    def test_unicode(self):
        data = '"Martin von Löwis","Marc André Lemburg","Guido van Rossum"\n'
        handler = CSV(string=data)
        rows = list(handler.get_rows())
        self.assertEqual(rows, [["Martin von Löwis", "Marc André Lemburg",
                                 "Guido van Rossum"]])


    def test_num_of_lines(self):
        handler = CSV(string=TEST_DATA_2)
        rows = list(handler.get_rows())
        self.assertEqual(len(rows), 3)


    def test_num_of_lines_with_last_new_line(self):
        data = TEST_DATA_2 + '\r\n'
        handler = CSV(string=data)
        rows = list(handler.get_rows())
        self.assertEqual(len(rows), 3)


    def test_load_state_with_schema(self):
        handler = Languages()
        handler.load_state_from_string(TEST_DATA_1)
        rows = list(handler.get_rows())
        self.assertEqual(rows, [
            [u"python", URI.decode('http://python.org'), 52343,
             Date.decode('2003-10-23')],
            [u"ruby", URI.decode('http://ruby-lang.org'), 42352,
             Date.decode('2001-03-28')]])


    def test_load_state_without_schema(self):
        handler = CSV(string=TEST_DATA_1)
        rows = list(handler.get_rows())
        self.assertEqual(rows, [
            ["python", 'http://python.org/', '52343', '2003-10-23'],
            ["ruby", 'http://ruby-lang.org/', '42352', '2001-03-28']])


    def test_to_str_with_schema(self):
        handler = Languages()
        handler.load_state_from_string(TEST_DATA_1)
        self.assertEqual(
            handler.to_str(),
            '"python","http://python.org/","52343","2003-10-23"\n'
            '"ruby","http://ruby-lang.org/","42352","2001-03-28"')


    def test_to_str_without_schema(self):
        handler = CSV(string=TEST_DATA_1)
        self.assertEqual(
            handler.to_str(),
            u'"python","http://python.org/","52343","2003-10-23"\n'
            u'"ruby","http://ruby-lang.org/","42352","2001-03-28"')


    def test_get_row(self):
        handler = CSV(string=TEST_DATA_2)
        self.assertEqual(handler.get_row(1), ['four', 'five', 'six'])


    def test_get_rows(self):
        handler = CSV(string=TEST_DATA_2)
        rows = list(handler.get_rows([0, 1]))
        self.assertEqual(rows, [['one', 'two', 'three'],
                                ['four', 'five', 'six']])


    def test_add_row(self):
        handler = CSV(string=TEST_DATA_2)
        handler.add_row(['a', 'b', 'c'])
        self.assertEqual(handler.get_row(3), ['a', 'b', 'c'])


    def test_del_row(self):
        handler = CSV(string=TEST_DATA_2)
        handler.del_row(1)
        self.assertRaises(IndexError, handler.get_row, 1)


    def test_del_rows(self):
        handler = CSV(string=TEST_DATA_2)
        handler.del_rows([0, 1])
        self.assertRaises(IndexError, handler.get_row, 0)


    def test_set_state_in_memory_resource(self):
        handler = CSV(string=TEST_DATA_2)
        handler.add_row(['a', 'b', 'c'])
        data = handler.to_str()

        handler2 = CSV(string=data)
        self.assertEqual(handler2.get_row(3), ['a', 'b', 'c'])


    def test_set_state_in_file_resource(self):
        handler = CSV('test.csv')
        handler.add_row(['d1', 'e1', 'f1'])
        handler.save_state()

        handler2 = CSV('test.csv')
        self.assertEqual(handler2.get_row(3), ['d1', 'e1', 'f1'])
        handler2.del_row(3)
        handler2.save_state()

        handler = CSV('test.csv')
        self.assertEqual(handler.get_nrows(), 3)


    def test_indexes_hit_in_one_row(self):
        handler = Languages()
        handler.load_state_from_string(TEST_DATA_1)
        self.assertEqual(handler.search(number=52343), [0])
        self.assertEqual(handler.search(date=Date.decode('2001-03-28')), [1])


    def test_indexes_hit_in_many_rows(self):
        data = 'house,2005-10-10\nwindow,2005-05-10\ncomputer,2005-10-10'
        handler = Things(string=data)
        handler.load_state_from_string(data)
        self.assertEqual(handler.search(date=Date.decode('2005-01-01')), [])
        self.assertEqual(handler.search(date=Date.decode('2005-10-10')), [0,2])


    def test_index_new_row(self):
        data = 'house,2005-10-10\nwindow,2005-05-10\ncomputer,2005-10-10'
        handler = Things()
        handler.load_state_from_string(data)
        handler.add_row(['flower', Date.decode('2005-05-10')])
        self.assertEqual(handler.search(date=Date.decode('2005-05-10')), [1,3])


    def test_index_del_row(self):
        data = 'house,2005-10-10\nwindow,2005-05-10\ncomputer,2005-10-10'
        handler = Things()
        handler.load_state_from_string(data)

        self.assertEqual(handler.search(name='window'), [1])
        handler.del_row(1)
        self.assertEqual(handler.search(name='window'), [])
        self.assertEqual(handler.search(name='computer'), [2])
        handler.del_row(2)
        self.assertEqual(handler.search(name='computer'), [])


    def test_build_csv_data(self):
        handler = People()
        handler.load_state_from_string('')
        handler.add_row(['Piotr', 'Macuk', '1975-12-08'])
        handler.add_row(['Basia', 'Macuk', '2002-02-14'])
        self.assertEqual(handler.search(surname='macuk'), [0, 1])
        handler.add_row(['Pawe³', 'Macuk', '1977-05-13'])
        self.assertEqual(handler.search(surname='macuk'), [0, 1, 2])
        handler.del_row(2)
        self.assertEqual(handler.search(surname='macuk'), [0, 1])
        handler.del_row(0)
        self.assertEqual(handler.search(surname='macuk'), [1])


    def test_advanced_search(self):
        handler = Countries()
        handler.load_state_from('test_adv.csv')
        result1 = handler.search(name='dde', country='sweden')
        self.assertEqual(result1, [5, 6])

        q1 = OrQuery(EqQuery('name', 'dde'), EqQuery('name', 'fse'))
        q2 = EqQuery('country', 'france')
        q3 = AndQuery(q1, q2)
        result2 = handler.search(q3)
        self.assertEqual(result2, [4])

        # previous results as query items
        q1 = OrQuery(EqQuery('name', 'dde'), EqQuery('name', 'fse'))
        q2 = OrQuery(EqQuery('country', 'poland'),
                     EqQuery('country', 'france'))
        q = AndQuery(q1, q2)
        result5 = handler.search(q)
        self.assertEqual(result5, [1, 4])


    def test_search_boolean(self):
        handler = Politicians()
        handler.load_state_from_string(
            '"Chavez","1"\n'
            '"Bush","0"\n')

        self.assertEqual(handler.search(is_good=True), [0])
        self.assertEqual(handler.search(is_good=False), [1])


    def test_access_by_name(self):
        handler = Languages()
        handler.load_state_from_string(TEST_DATA_1)

        row = handler.get_row(1)
        self.assertEqual(row.get_value('name'), u'ruby')


    def test_bad_syntax_csv_file(self):
        load_state = CSV().load_state_from_string
        self.assertRaises(ValueError, load_state, TEST_SYNTAX_ERROR)


    def test_bad_syntax_csv_file_with_schema(self):
        handler = Numbers()
        load_state = handler.load_state_from_string
        self.assertRaises(ValueError, load_state, TEST_SYNTAX_ERROR)



if __name__ == '__main__':
    unittest.main()
