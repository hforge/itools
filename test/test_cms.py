# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools
from itools.uri import get_absolute_reference2
from itools import vfs
from itools.handlers import get_handler
from itools.handlers.Text import Text
from itools.cms.database import DatabaseFS



class BrokenHandler(Text):
    
    def to_str(self):
        iamsobroken




class DatabaseTestCase(TestCase):

    def setUp(self):
        database = DatabaseFS('.')
        self.database = database
        self.root = database.root


    def tearDown(self):
        if vfs.exists('fables/31.txt'):
            vfs.remove('fables/31.txt')


    def test_abort(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.copy_handler()
        fables.set_handler('31.txt', fable)
        # Abort
        self.database.abort()
        # Test
        fables = get_handler('fables')
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
        fables = get_handler('fables')
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
        fables = get_handler('fables')
        self.assertEqual(fables.has_handler('31.txt'), False)
        self.assertEqual(fables.has_handler('broken.txt'), False)



 
if __name__ == '__main__':
    unittest.main()
