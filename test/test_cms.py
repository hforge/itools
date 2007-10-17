# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.uri import get_absolute_reference2
from itools.datatypes import Unicode
from itools import vfs
from itools.handlers import get_handler, Text, Table
from itools.cms.database import DatabaseFS



class BrokenHandler(Text):

    def to_str(self):
        iamsobroken



class Agenda(Table):
    schema = {'firstname': Unicode(index='text', multiple=False),
              'lastname': Unicode(multiple=False)}



class DatabaseTestCase(TestCase):

    def setUp(self):
        database = DatabaseFS('.')
        self.database = database
        self.root = database.root


    def tearDown(self):
        for name in ['31.txt', 'agenda']:
            if vfs.exists('database/%s' % name):
                vfs.remove('database/%s' % name)


    def test_abort(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.copy_handler()
        fables.set_handler('31.txt', fable)
        # Abort
        self.database.abort()
        # Test
        fables = get_handler('database')
        self.assertEqual(fables.has_handler('31.txt'), False)


    def test_commit(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.copy_handler()
        fables.set_handler('31.txt', fable)
        # Commit
        self.database.commit()
        # Test
        fables = get_handler('database')
        self.assertEqual(fables.has_handler('31.txt'), True)


    def test_broken_commit(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.copy_handler()
        fables.set_handler('31.txt', fable)
        # Add broken handler
        broken = BrokenHandler()
        fables.set_handler('broken.txt', broken)
        # Commit
        self.assertRaises(NameError, self.database.commit)
        # Test
        fables = get_handler('database')
        self.assertEqual(fables.has_handler('31.txt'), False)
        self.assertEqual(fables.has_handler('broken.txt'), False)


    def test_append(self):
        # Initalize
        root = self.root
        agenda = Agenda()
        agenda.add_record({'firstname': u'Karl', 'lastname': u'Marx'})
        agenda.add_record({'firstname': u'Jean-Jacques',
                           'lastname': u'Rousseau'})
        root.set_handler('agenda', agenda)
        self.database.commit()
        # Work
        agenda = Agenda(root.get_handler('agenda').uri)
        fake = agenda.add_record({'firstname': u'Toto', 'lastname': u'Fofo'})
        agenda.add_record({'firstname': u'Albert', 'lastname': u'Einstein'})
        self.database.commit()
        agenda.del_record(fake.id)
        self.database.commit()
        # Test
        agenda = Agenda(root.get_handler('agenda').uri)
        ids = [ x.id for x in agenda.search(firstname=u'Toto') ]
        self.assertEqual(len(ids), 0)
        ids = [ x.id for x in agenda.search(firstname=u'Albert') ]
        self.assertEqual(len(ids), 1)
        ids = [ x.id for x in agenda.search(firstname=u'Jean') ]
        self.assertEqual(len(ids), 1)



if __name__ == '__main__':
    unittest.main()
