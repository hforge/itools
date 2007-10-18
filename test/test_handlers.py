# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Luis Arturo Belmar-Letelier <luis@itaapy.com>
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools import vfs
from itools.datatypes import Unicode
from itools.handlers import get_handler, Database, Text, Table
from itools.handlers.table import unfold_lines


class StateTestCase(TestCase):

    def test_abort(self):
        handler = get_handler('tests/hello.txt')
        self.assertEqual(handler.data, u'hello world\n')
        handler.set_data(u'bye world\n')
        self.assertEqual(handler.data, u'bye world\n')
        handler.abort_changes()
        self.assertEqual(handler.data, u'hello world\n')



class FolderTestCase(TestCase):

    def setUp(self):
        database = Database()
        self.database = database
        root = get_handler('.')
        root.database = database
        self.root = root
        file = vfs.make_file('tests/toto.txt')
        try:
            file.write('I am Toto\n')
        finally:
            file.close()


    def tearDown(self):
        if vfs.exists('tests/toto.txt'):
            vfs.remove('tests/toto.txt')


    def test_remove(self):
        folder = self.root.get_handler('tests')
        folder.del_handler('toto.txt')
        self.assertEqual(vfs.exists('tests/toto.txt'), True)
        self.assertEqual(folder.has_handler('toto.txt'), False)
        # Save
        self.database.save_changes()
        self.assertEqual(vfs.exists('tests/toto.txt'), False)
        self.assertEqual(folder.has_handler('toto.txt'), False)


    def test_remove_add(self):
        folder = self.root.get_handler('tests')
        folder.del_handler('toto.txt')
        folder.set_handler('toto.txt', Text())
        self.assertEqual(vfs.exists('tests/toto.txt'), True)
        self.assertEqual(folder.has_handler('toto.txt'), True)
        # Save
        self.database.save_changes()
        self.assertEqual(vfs.exists('tests/toto.txt'), True)
        self.assertEqual(folder.has_handler('toto.txt'), True)


    def test_remove_add_remove(self):
        folder = self.root.get_handler('tests')
        folder.del_handler('toto.txt')
        folder.set_handler('toto.txt', Text())
        folder.del_handler('toto.txt')
        self.assertEqual(vfs.exists('tests/toto.txt'), True)
        self.assertEqual(folder.has_handler('toto.txt'), False)
        # Save
        self.database.save_changes()
        self.assertEqual(vfs.exists('tests/toto.txt'), False)
        self.assertEqual(folder.has_handler('toto.txt'), False)


    def test_remove_remove(self):
        folder = self.root.get_handler('tests')
        folder.del_handler('toto.txt')
        self.assertRaises(Exception, folder.del_handler, 'toto.txt')


    def test_remove_add_add(self):
        folder = self.root.get_handler('tests')
        folder.del_handler('toto.txt')
        folder.set_handler('toto.txt', Text())
        self.assertRaises(Exception, folder.set_handler, 'toto.txt', Text())


    def test_remove_abort(self):
        database = self.database
        folder = self.root.get_handler('tests')
        self.assertEqual(folder.has_handler('toto.txt'), True)
        folder.del_handler('toto.txt')
        self.assertEqual(folder.has_handler('toto.txt'), False)
        database.abort_changes()
        self.assertEqual(folder.has_handler('toto.txt'), True)
        # Save
        database.save_changes()
        self.assertEqual(vfs.exists('tests/toto.txt'), True)


    def test_add_abort(self):
        database = self.database
        folder = self.root.get_handler('tests')
        self.assertEqual(folder.has_handler('fofo.txt'), False)
        folder.set_handler('fofo.txt', Text())
        self.assertEqual(folder.has_handler('fofo.txt'), True)
        database.abort_changes()
        self.assertEqual(folder.has_handler('fofo.txt'), False)
        # Save
        database.save_changes()
        self.assertEqual(vfs.exists('tests/fofo.txt'), False)



class TextTestCase(TestCase):

    def test_load_file(self):
        handler = get_handler('tests/hello.txt')
        self.assertEqual(handler.data, u'hello world\n')


###########################################################################
# Safe transactions
###########################################################################
class BrokenHandler(Text):

    def to_str(self):
        iamsobroken



class DatabaseTestCase(TestCase):

    def setUp(self):
        database = Database('database.commit')
        self.database = database
        root = get_handler('fables')
        root.database = database
        self.root = root


    def tearDown(self):
        for name in ['fables/31.txt', 'fables/agenda', 'database.commit']:
            if vfs.exists(name):
                vfs.remove(name)


    def test_abort(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.clone()
        fables.set_handler('31.txt', fable)
        # Abort
        self.database.abort_changes()
        # Test
        self.assertEqual(vfs.exists('fables/31.txt'), False)


    def test_commit(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.clone()
        fables.set_handler('31.txt', fable)
        # Commit
        self.database.save_changes()
        # Test
        self.assertEqual(vfs.exists('fables/31.txt'), True)


    def test_broken_commit(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.clone()
        fables.set_handler('31.txt', fable)
        # Add broken handler
        broken = BrokenHandler()
        fables.set_handler('broken.txt', broken)
        # Commit
        self.assertRaises(NameError, self.database.save_changes)
        # Test
        self.assertEqual(vfs.exists('fables/31.txt'), False)
        self.assertEqual(vfs.exists('fables/broken.txt'), False)


    def test_append(self):
        database = self.database
        root = self.root
        # Initalize
        agenda = Agenda()
        agenda.add_record({'firstname': u'Karl', 'lastname': u'Marx'})
        agenda.add_record({'firstname': u'Jean-Jacques',
                           'lastname': u'Rousseau'})
        root.set_handler('agenda', agenda)
        database.save_changes()
        # Work
        agenda = root.get_handler('agenda')
        fake = agenda.add_record({'firstname': u'Toto', 'lastname': u'Fofo'})
        agenda.add_record({'firstname': u'Albert', 'lastname': u'Einstein'})
        database.save_changes()
        agenda.del_record(fake.id)
        database.save_changes()
        # Test
        agenda = root.get_handler('agenda')
        ids = [ x.id for x in agenda.search(firstname=u'Toto') ]
        self.assertEqual(len(ids), 0)
        ids = [ x.id for x in agenda.search(firstname=u'Albert') ]
        self.assertEqual(len(ids), 1)
        ids = [ x.id for x in agenda.search(firstname=u'Jean') ]
        self.assertEqual(len(ids), 1)



##########################################################################
# The Table handler
##########################################################################

agenda_file = """id:0/0
ts:2007-07-13T17:19:21
firstname:Karl
lastname:Marx

id:1/0
ts:2007-07-14T16:43:49
firstname:Jean-Jacques
lastname:Rousseau
"""


class Agenda(Table):
    __slots__ = Table.__slots__
    schema = {'firstname': Unicode(index='text', multiple=False),
              'lastname': Unicode(multiple=False)}


class TableTestCase(TestCase):

    def tearDown(self):
        if vfs.exists('tests/agenda'):
            vfs.remove('tests/agenda')


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

        i = 0
        for line in output:
            self.assertEqual(line, expected[i])
            i = i + 1


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



if __name__ == '__main__':
    unittest.main()
