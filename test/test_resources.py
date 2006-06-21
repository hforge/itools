# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import datetime
import os
import unittest
from unittest import TestCase

# Import from itools
from itools.resources import file, http, memory, zodb, get_resource

# Import from the ZODB
from ZODB.FileStorage import FileStorage



class FileTestCase(TestCase):

    def setUp(self):
        self.tests = get_resource('tests')


    def test_has_resource(self):
        self.assertEqual(self.tests.has_resource('index.html.en'), True)


    def test_has_not_resource(self):
        self.assertEqual(self.tests.has_resource('index.html.es'), False)


    def test_link(self):
        c = self.tests.get_resource('c')
        tests = c.get_resource('..')
        self.assertEqual('c' in tests.get_names(), True)


##    def test_python(self):
##        resource = get_resource('base.py')
##        self.assertEqual(resource.get_mimetype(), 'text/x-python')


##    def test_html(self):
##        resource = get_resource('tests/index.html.en')
##        self.assertEqual(resource.get_mimetype(), 'text/html')


##    def test_folder(self):
##        folder = get_resource('tests')
##        self.assertEqual(folder.get_mimetype(), 'application/x-not-regular-file')



class ZODBTestCase(TestCase):

    def setUp(self):
        storage = FileStorage('test_db.fs')
        self.database = zodb.Database(storage)


    def tearDown(self):
        os.system('rm test_db.fs*')


    def test_add_file(self):
        root = self.database.get_resource('/')
        root.set_resource('test.txt', memory.File('hello'))

        new_resource = root.get_resource('test.txt')
        self.assertEqual(new_resource.read(), 'hello')

        root.get_transaction().abort()


    def test_add_folder(self):
        root = self.database.get_resource('/')
        root.set_resource('test', memory.Folder())

        self.assertEqual(root.has_resource('test'), True)

        root.get_transaction().abort()


    def test_abort_transaction(self):
        root = self.database.get_resource('/')
        root.set_resource('test.txt', memory.File('hello'))

        self.assertEqual(root.has_resource('test.txt'), True)

        transaction = root.get_transaction()
        transaction.abort()

        self.assertEqual(root.has_resource('test.txt'), False)


    def test_populate(self):
        root = self.database.get_resource('/')
        tests = get_resource('tests')
        root.set_resource('tests', tests)

        self.assertEqual(root.has_resource('tests/index.html.en'), True)


    def test_mtime(self):
        root = self.database.get_resource('/')
        tests = get_resource('tests')
        root.set_resource('tests', tests)
        root.get_transaction().commit()
        now = datetime.now()
        mtime = root.get_resource('tests/index.html.en').get_mtime()
        self.assertEqual(mtime.toordinal(), now.toordinal())



if __name__ == '__main__':
    unittest.main()
