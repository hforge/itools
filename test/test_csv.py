# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Piotr Macuk <piotr@macuk.pl>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.datatypes import Boolean, Date, Integer, Unicode, URI, String
from itools.csv import CSVFile, Table, UniqueError
from itools.csv.table import unfold_lines
from itools import vfs
from itools.xapian import AndQuery, OrQuery, PhraseQuery


TEST_DATA_1 = """python,http://python.org/,52343,2003-10-23
ruby,http://ruby-lang.org/,42352,2001-03-28"""

TEST_DATA_2 = 'one,two,three\nfour,five,six\nseven,eight,nine'

TEST_SYNTAX_ERROR = '"one",,\n,"two",,\n,,"three"'



class Languages(CSVFile):

    columns = ['name', 'url', 'number', 'date']
    schema = {'name': Unicode,
              'url': URI,
              'number': Integer(is_indexed=True),
              'date': Date(is_indexed=True)}


class Things(CSVFile):

    columns = ['name', 'date']
    schema = {'name': Unicode(is_indexed=True), 'date': Date(is_indexed=True)}


class Numbers(CSVFile):

    columns = ['one', 'two', 'three']
    schema = {'one': Unicode, 'two': Unicode, 'three': Unicode}


class People(CSVFile):

    columns = ['name', 'surname', 'date']
    schema = {'name': Unicode,
              'surname': Unicode(is_indexed=True),
              'date': Date(is_indexed=True)}


class Countries(CSVFile):

    class_csv_guess = True
    columns = ['id', 'name', 'country', 'date']
    schema = {'id': Integer,
              'name': Unicode(is_indexed=True),
              'country': Unicode(is_indexed=True),
              'date': Date(is_indexed=True)}


class Politicians(CSVFile):

    columns = ['name', 'is_good']
    schema = {'name': Unicode, 'is_good': Boolean(is_indexed=True)}




class CSVTestCase(TestCase):

    def test_unicode(self):
        data = '"Martin von Löwis","Marc André Lemburg","Guido van Rossum"\n'
        handler = CSVFile(string=data)
        rows = list(handler.get_rows())
        self.assertEqual(rows, [["Martin von Löwis", "Marc André Lemburg",
                                 "Guido van Rossum"]])


    def test_num_of_lines(self):
        handler = CSVFile(string=TEST_DATA_2)
        rows = list(handler.get_rows())
        self.assertEqual(len(rows), 3)


    def test_num_of_lines_with_last_new_line(self):
        data = TEST_DATA_2 + '\r\n'
        handler = CSVFile(string=data)
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


    def test_load_state_without_schema_and_columns(self):
        handler = CSVFile(string=TEST_DATA_1)
        rows = list(handler.get_rows())
        self.assertEqual(rows, [
            ["python", 'http://python.org/', '52343', '2003-10-23'],
            ["ruby", 'http://ruby-lang.org/', '42352', '2001-03-28']])


    def test_load_state_without_schema(self):
        handler = CSVFile()
        handler.columns = ['name', 'url', 'number', 'date']
        handler.load_state_from_string(TEST_DATA_1)
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
        handler = CSVFile(string=TEST_DATA_1)
        self.assertEqual(
            handler.to_str(),
            u'"python","http://python.org/","52343","2003-10-23"\n'
            u'"ruby","http://ruby-lang.org/","42352","2001-03-28"')


    def test_get_row(self):
        handler = CSVFile(string=TEST_DATA_2)
        self.assertEqual(handler.get_row(1), ['four', 'five', 'six'])


    def test_get_rows(self):
        handler = CSVFile(string=TEST_DATA_2)
        rows = list(handler.get_rows([0, 1]))
        self.assertEqual(rows, [['one', 'two', 'three'],
                                ['four', 'five', 'six']])


    def test_add_row(self):
        handler = CSVFile(string=TEST_DATA_2)
        handler.add_row(['a', 'b', 'c'])
        self.assertEqual(handler.get_row(3), ['a', 'b', 'c'])


    def test_del_row(self):
        handler = CSVFile(string=TEST_DATA_2)
        handler.del_row(1)
        self.assertRaises(IndexError, handler.get_row, 1)


    def test_del_rows(self):
        handler = CSVFile(string=TEST_DATA_2)
        handler.del_rows([0, 1])
        self.assertRaises(IndexError, handler.get_row, 0)


    def test_set_state_in_memory_resource(self):
        handler = CSVFile(string=TEST_DATA_2)
        handler.add_row(['a', 'b', 'c'])
        data = handler.to_str()

        handler2 = CSVFile(string=data)
        self.assertEqual(handler2.get_row(3), ['a', 'b', 'c'])


    def test_set_state_in_file_resource(self):
        handler = CSVFile('tests/test.csv')
        handler.add_row(['d1', 'e1', 'f1'])
        handler.save_state()

        handler2 = CSVFile('tests/test.csv')
        self.assertEqual(handler2.get_row(3), ['d1', 'e1', 'f1'])
        handler2.del_row(3)
        handler2.save_state()

        handler = CSVFile('tests/test.csv')
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
        self.assertEqual(handler.search(date=Date.decode('2005-10-10')),
                         [0,2])


    def test_index_new_row(self):
        data = 'house,2005-10-10\nwindow,2005-05-10\ncomputer,2005-10-10'
        handler = Things()
        handler.load_state_from_string(data)
        handler.add_row(['flower', Date.decode('2005-05-10')])
        self.assertEqual(handler.search(date=Date.decode('2005-05-10')),
                         [1,3])


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
        handler.add_row(['Piotr', 'Macuk', Date.decode('1975-12-08')])
        handler.add_row(['Basia', 'Macuk', Date.decode('2002-02-14')])
        self.assertEqual(handler.search(surname='macuk'), [0, 1])
        handler.add_row(['Pawe³', 'Macuk', Date.decode('1977-05-13')])
        self.assertEqual(handler.search(surname='macuk'), [0, 1, 2])
        handler.del_row(2)
        self.assertEqual(handler.search(surname='macuk'), [0, 1])
        handler.del_row(0)
        self.assertEqual(handler.search(surname='macuk'), [1])


    def test_advanced_search(self):
        handler = Countries()
        handler.load_state_from('tests/test_adv.csv')
        result1 = handler.search(name='dde', country='sweden')
        self.assertEqual(result1, [5, 6])

        q1 = OrQuery(PhraseQuery('name', 'dde'), PhraseQuery('name', 'fse'))
        q2 = PhraseQuery('country', 'france')
        q3 = AndQuery(q1, q2)
        result2 = handler.search(q3)
        self.assertEqual(result2, [4])

        # previous results as query items
        q1 = OrQuery(PhraseQuery('name', 'dde'), PhraseQuery('name', 'fse'))
        q2 = OrQuery(PhraseQuery('country', 'poland'),
                     PhraseQuery('country', 'france'))
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
        load_state = CSVFile().load_state_from_string
        self.assertRaises(ValueError, load_state, TEST_SYNTAX_ERROR)


    def test_bad_syntax_csv_file_with_schema(self):
        handler = Numbers()
        load_state = handler.load_state_from_string
        self.assertRaises(ValueError, load_state, TEST_SYNTAX_ERROR)



##########################################################################
# The Table handler
##########################################################################

agenda_file = """id:0/0
ts:2007-07-13T17:19:21
firstname:Karl
lastname:Marx
email:karl@itaapy.com

id:1/0
ts:2007-07-14T16:43:49
firstname:Jean-Jacques
lastname:Rousseau
email:jacques@itaapy.com
"""


class Agenda(Table):

    record_schema = {
        'firstname': Unicode(is_indexed=True, multiple=False),
        'lastname': Unicode(multiple=False),
        'email': Unicode(is_indexed=True, multiple=False, unique=True)}


books_file = """id:0/0
ts:2007-07-13T17:19:21
title;language=de:Das Kapital
title;language=es:El Capital
"""


books_file_bad = """id:0/0
ts:2007-07-13T17:19:21
title;language=de:Das Kapital
title;language=es,fr:El Capital
"""


class Books(Table):

    record_schema = {
        'title': Unicode(multiple=True),
        'author': Unicode}

    parameters_schema = {
        'language': String(multiple=False)}



class TableTestCase(TestCase):

    def tearDown(self):
        for name in ['agenda', 'books']:
            name = 'tests/%s' % name
            if vfs.exists(name):
                vfs.remove(name)


    def test_unfolding(self):
        """Test unfolding lines."""
        input = (
            'BEGIN:VCALENDAR\n'
            'VERSION:2.0\n'
            'BEGIN:VEVENT\n'
            'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a\n'
            'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0\n'
            'DTSTART;VALUE=DATE:20050530\n'
            'DTEND;VALUE=DATE:20050531\n'
            'DTSTAMP:20050601T074604Z\n'
            'DESCRIPTION:opps !!! this is a really big information, ..., '
            'but does it change anything \n'
            ' in reality ?? We should see a radical change in the next \n'
            ' 3 months, shouldn\'t we ???\\nAaah !!!\n' )

        expected = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'BEGIN:VEVENT',
            'UID:581361a0-1dd2-11b2-9a42-bd3958eeac9a',
            'X-MOZILLA-RECUR-DEFAULT-INTERVAL:0',
            'DTSTART;VALUE=DATE:20050530',
            'DTEND;VALUE=DATE:20050531',
            'DTSTAMP:20050601T074604Z',
            'DESCRIPTION:opps !!! this is a really big information, ..., but'
            ' does it change anything in reality ?? We should see a radical'
            ' change in the next 3 months, shouldn\'t we ???\\nAaah !!!']

        output = unfold_lines(input)

        for i, line in enumerate(output):
            self.assertEqual(line, expected[i])


    def test_de_serialize(self):
        data = ('id:0/0\n'
                'ts:2007-07-13T17:19:21\n'
                '\n'
                'id:1/0\n'
                'title;language=en:hello\n'
                'title;language=es:hola\n'
                'ts:2007-07-14T16:43:49\n'
                '\n')
        table = Table(string=data)
        self.assertEqual(table.to_str(), data)


    def test_multiple(self):
        self.assertRaises(Exception, Agenda, string=
            'id:0/0\n'
            'ts:2007-07-13T17:19:21\n'
            'firstname:Karl\n'
            'firstname:Marx\n')


    def test_search(self):
        agenda = Agenda(string=agenda_file)
        ids = [ x.id for x in agenda.search(firstname=u'Jean') ]
        self.assertEqual(ids, [1])


    def test_save(self):
        agenda = Agenda(string=agenda_file)
        agenda.save_state_to('tests/agenda')
        # Change
        agenda = Agenda('tests/agenda')
        fake = agenda.add_record({'firstname': u'Toto', 'lastname': u'Fofo'})
        agenda.add_record({'firstname': u'Albert', 'lastname': u'Einstein'})
        agenda.del_record(fake.id)
        agenda.save_state()
        # Test
        agenda = Agenda('tests/agenda')
        ids = [ x.id for x in agenda.search(firstname=u'Toto') ]
        self.assertEqual(len(ids), 0)
        ids = [ x.id for x in agenda.search(firstname=u'Albert') ]
        self.assertEqual(len(ids), 1)
        # Clean
        vfs.remove('tests/agenda')


    def test_unique(self):
        agenda = Agenda(string=agenda_file)
        email = 'karl@itaapy.com'
        # Add
        record = {'firstname': 'Karl', 'lastname': 'Smith', 'email': email}
        self.assertRaises(UniqueError, agenda.add_record, record)
        # Update
        self.assertRaises(UniqueError, agenda.update_record, 1, email=email)


    def test_parameters_bad(self):
        self.assertRaises(ValueError, Books, string=books_file_bad)


    def test_parameters_load(self):
        table = Books(string=books_file)
        record_0 = table.get_record(0)
        value = table.get_record_value(record_0, 'title', language='es')
        self.assertEqual(value, u'El Capital')


    def test_parameters_save(self):
        table = Books(string=books_file)
        table.save_state_to('tests/books')
        # Load
        table = Books('tests/books')
        table.load_state()
        # Test
        record_0 = table.get_record(0)
        value = table.get_record_value(record_0, 'title', language='es')
        self.assertEqual(value, u'El Capital')



if __name__ == '__main__':
    unittest.main()
