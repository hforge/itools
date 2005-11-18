# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from datetime import datetime
import os
import unittest
from unittest import TestCase

# Import from itools
from __init__ import get_resource
import memory
import zodb

# Import from the ZODB
from ZODB.FileStorage import FileStorage


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
