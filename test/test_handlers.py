# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Nicolas Deram <nderam@gmail.com>
# Copyright (C) 2008 Gautier Hayoun <gautier.hayoun@supinfo.com>
# Copyright (C) 2008, 2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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
from unittest import TestCase, main

# Import from itools
from itools.handlers import RODatabase
from itools.handlers import ConfigFile, TGZFile
from itools.fs import lfs


ro_database = RODatabase(fs=lfs)


class StateTestCase(TestCase):

    def test_abort(self):
        handler = ro_database.get_handler('tests/hello.txt')
        self.assertEqual(handler.data, u'hello world\n')
        handler.set_data(u'bye world\n')
        self.assertEqual(handler.data, u'bye world\n')
        handler.abort_changes()
        self.assertEqual(handler.data, u'hello world\n')



class ConfigFileTestCase(TestCase):
    """ still need to complete the tests with schema """

    def setUp(self):
        self.config_path = "tests/setup.conf.test"
        if lfs.exists(self.config_path):
            lfs.remove(self.config_path)


    def tearDown(self):
        if lfs.exists(self.config_path):
            lfs.remove(self.config_path)


    def _init_test(self, value):
        # Init data
        if not lfs.exists(self.config_path):
            lfs.make_file(self.config_path)

        # Write data
        config = ro_database.get_handler(self.config_path, ConfigFile)
        config.set_value("test", value)
        config.save_state()


    def test_simple_value(self):
        # Init data
        value = "HELLO, WORLD!"
        self._init_test(value)

        # Read data
        config2 = ro_database.get_handler(self.config_path, ConfigFile)
        config2_value = config2.get_value("test")
        lfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)


    def test_long_value(self):
        # Init data
        value = "HELLO, WORLD!\n\nHELLO WORLD2222"
        self._init_test(value)

        # Read data
        config2 = ro_database.get_handler(self.config_path, ConfigFile)
        try:
            config2_value = config2.get_value("test")
        except SyntaxError, e:
            self.fail(e)
        finally:
            lfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)


    def test_last_line_empty(self):
        # Init data
        value = "HELLO, WORLD!\n\n"
        self._init_test(value)

        # Write data
        config = ro_database.get_handler(self.config_path, ConfigFile)
        config.set_value("test", value)
        config.save_state()

        # Read data
        config2 = ro_database.get_handler(self.config_path, ConfigFile)
        config2_value = config2.get_value("test")
        lfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)


    def test_quote_value(self):
        # Init data
        value = "HELLO, \"WORLD\"!"
        self._init_test(value)

        # Write data
        config = ro_database.get_handler(self.config_path, ConfigFile)
        try:
            config.set_value("test", value)
        except SyntaxError, e:
            self.fail(e)
        config.save_state()

        # Read data
        config2 = ro_database.get_handler(self.config_path, ConfigFile)
        try:
            config2_value = config2.get_value("test")
        except SyntaxError, e:
            self.fail(e)
        finally:
            lfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)



    def test_wrapped_quote_value(self):
        # Init data
        value = "\"HELLO, WORLD!\""
        self._init_test(value)

        # Write data
        config = ro_database.get_handler(self.config_path, ConfigFile)
        try:
            config.set_value("test", value)
        except SyntaxError, e:
            self.fail(e)
        config.save_state()

        # Read data
        config2 = ro_database.get_handler(self.config_path, ConfigFile)
        try:
            config2_value = config2.get_value("test")
        except SyntaxError, e:
            self.fail(e)
        finally:
            lfs.remove(self.config_path)

        # Test data
        self.assertEqual(config2_value, value)


###########################################################################
# Archive files
###########################################################################
class ArchiveTestCase(TestCase):

    def test_get_handler(self):
        cls = ro_database.get_handler_class('handlers/test.tar.gz')
        self.assertEqual(cls, TGZFile)

        file = ro_database.get_handler('handlers/test.tar.gz')
        self.assertEqual(file.__class__, TGZFile)



if __name__ == '__main__':
    main()
