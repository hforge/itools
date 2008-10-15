# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Nicolas Deram <nicolas@itaapy.com>
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
from itools.csv import Table
from itools.datatypes import Unicode
from itools.handlers import get_handler, Database, SafeDatabase, TextFile
from itools.handlers import ConfigFile
from itools.uri import get_reference
from itools import vfs



class Agenda(Table):

    record_schema = {'firstname': Unicode(index='text', multiple=False),
                     'lastname': Unicode(multiple=False)}



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
        folder = vfs.open('tests')
        for name in 'toto.txt', 'fofo.txt', 'fofo2.txt', 'empty':
            if folder.exists(name):
                folder.remove(name)


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
        folder.set_handler('toto.txt', TextFile())
        self.assertEqual(vfs.exists('tests/toto.txt'), True)
        self.assertEqual(folder.has_handler('toto.txt'), True)
        # Save
        self.database.save_changes()
        self.assertEqual(vfs.exists('tests/toto.txt'), True)
        self.assertEqual(folder.has_handler('toto.txt'), True)


    def test_remove_add_remove(self):
        folder = self.root.get_handler('tests')
        folder.del_handler('toto.txt')
        folder.set_handler('toto.txt', TextFile())
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
        folder.set_handler('toto.txt', TextFile())
        self.assertRaises(Exception, folder.set_handler, 'toto.txt',
                          TextFile())


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
        folder.set_handler('fofo.txt', TextFile())
        self.assertEqual(folder.has_handler('fofo.txt'), True)
        database.abort_changes()
        self.assertEqual(folder.has_handler('fofo.txt'), False)
        # Save
        database.save_changes()
        self.assertEqual(vfs.exists('tests/fofo.txt'), False)


    def test_add_copy(self):
        database = self.database
        folder = self.root.get_handler('tests')
        folder.set_handler('fofo.txt', TextFile())
        folder.copy_handler('fofo.txt', 'fofo2.txt')
        # Save
        database.save_changes()
        self.assertEqual(vfs.exists('tests/fofo2.txt'), True)


    def test_del_change(self):
        """Cannot change removed files.
        """
        folder = self.root.get_handler('tests')
        file = folder.get_handler('toto.txt')
        folder.del_handler('toto.txt')
        self.assertRaises(RuntimeError, file.set_data, u'Oh dear\n')


    def test_nocache_change(self):
        """Only can change cached files.
        """
        self.database.set_use_cache(False)
        file = self.root.get_handler('tests/toto.txt')
        self.database.set_use_cache(True)
        self.assertRaises(RuntimeError, file.set_data, u'Oh dear\n')


    def test_empty_folder(self):
        """Empty folders do not exist.
        """
        database = self.database
        root = self.root
        # Setup
        root.set_handler('tests/empty/toto.txt', TextFile())
        database.save_changes()
        root.del_handler('tests/empty/toto.txt')
        database.save_changes()
        self.assertEqual(vfs.exists('tests/empty'), True)
        # Test
        root.set_handler('tests/empty', TextFile())
        database.save_changes()
        self.assertEqual(vfs.is_file('tests/empty'), True)


    def test_not_empty_folder(self):
        """Empty folders do not exist.
        """
        database = self.database
        root = self.root
        # Setup
        root.set_handler('tests/empty/toto.txt', TextFile())
        database.save_changes()
        # Test
        self.assertRaises(RuntimeError, root.set_handler, 'tests/empty',
                          TextFile())



class TextTestCase(TestCase):

    def test_load_file(self):
        handler = get_handler('tests/hello.txt')
        self.assertEqual(handler.data, u'hello world\n')



class ConfigFileTestCase(TestCase):
    """ still need to complete the tests with schema """

    def setUp(self):
        self.config_path = "tests/setup.conf.test"
        if vfs.exists(self.config_path):
            vfs.remove(self.config_path)


    def tearDown(self):
        if vfs.exists(self.config_path):
            vfs.remove(self.config_path)


    def _init_test(self, value):
        # Init data
        if not vfs.exists(self.config_path):
            vfs.make_file(self.config_path)

        # Write data
        config = ConfigFile(ref=self.config_path)
        config.set_value("test", value)
        config.save_state()


    def test_simple_value(self):
        # Init data
        value = "HELLO, WORLD!"
        self._init_test(value)

        # Read data
        config2 = ConfigFile(ref=self.config_path)
        config2_value = config2.get_value("test")
        vfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)


    def test_long_value(self):
        # Init data
        value = "HELLO, WORLD!\n\nHELLO WORLD2222"
        self._init_test(value)

        # Read data
        config2 = ConfigFile(ref=self.config_path)
        try:
            config2_value = config2.get_value("test")
        except SyntaxError, e:
            self.fail(e)
        finally:
            vfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)


    def test_last_line_empty(self):
        # Init data
        value = "HELLO, WORLD!\n\n"
        self._init_test(value)

        # Write data
        config = ConfigFile(ref=self.config_path)
        config.set_value("test", value)
        config.save_state()

        # Read data
        config2 = ConfigFile(ref=self.config_path)
        config2_value = config2.get_value("test")
        vfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)


    def test_quote_value(self):
        # Init data
        value = "HELLO, \"WORLD\"!"
        self._init_test(value)

        # Write data
        config = ConfigFile(ref=self.config_path)
        try:
            config.set_value("test", value)
        except SyntaxError, e:
            self.fail(e)
        config.save_state()

        # Read data
        config2 = ConfigFile(ref=self.config_path)
        try:
            config2_value = config2.get_value("test")
        except SyntaxError, e:
            self.fail(e)
        finally:
            vfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)



    def test_wrapped_quote_value(self):
        # Init data
        value = "\"HELLO, WORLD!\""
        self._init_test(value)

        # Write data
        config = ConfigFile(ref=self.config_path)
        try:
            config.set_value("test", value)
        except SyntaxError, e:
            self.fail(e)
        config.save_state()

        # Read data
        config2 = ConfigFile(ref=self.config_path)
        try:
            config2_value = config2.get_value("test")
        except SyntaxError, e:
            self.fail(e)
        finally:
            vfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)



###########################################################################
# Safe transactions
###########################################################################
class BrokenHandler(TextFile):

    def to_str(self):
        iamsobroken



class DatabaseTestCase(TestCase):

    def setUp(self):
        database = SafeDatabase('database.commit')
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


    def test_remove_add(self):
        fables = self.root
        # Firstly add 31.txt
        fables.set_handler('31.txt', TextFile())
        self.database.save_changes()

        fables.del_handler('31.txt')
        fables.set_handler('31.txt', TextFile())
        self.assertEqual(vfs.exists('fables/31.txt'), True)
        self.assertEqual(fables.has_handler('31.txt'), True)
        # Save
        self.database.save_changes()
        self.assertEqual(vfs.exists('fables/31.txt'), True)
        self.assertEqual(fables.has_handler('31.txt'), True)



if __name__ == '__main__':
    unittest.main()
