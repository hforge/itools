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
from unittest import TestCase, main

# Import from itools
from itools.core import start_subprocess
from itools.database import make_git_database
from itools.handlers import TextFile
from itools.fs import lfs



class BrokenHandler(TextFile):

    def to_str(self):
        iamsobroken



class GitDatabaseTestCase(TestCase):

    def setUp(self):
        database = make_git_database('fables', 20, 20)
        self.database = database
        root = database.get_handler('.')
        self.root = root


    def tearDown(self):
        for name in ['fables/31.txt', 'fables/agenda', 'fables/.git',
                     'fables/broken.txt']:
            if lfs.exists(name):
                lfs.remove(name)


    def test_abort(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.clone()
        fables.set_handler('31.txt', fable)
        # Abort
        self.database.abort_changes()
        # Test
        self.assertEqual(lfs.exists('fables/31.txt'), False)


    def test_commit(self):
        # Changes (copy&paste)
        fables = self.root
        fable = fables.get_handler('30.txt')
        fable = fable.clone()
        fables.set_handler('31.txt', fable)
        # Commit
        self.database.save_changes()
        # Test
        self.assertEqual(lfs.exists('fables/31.txt'), True)


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
        self.assertEqual(lfs.exists('fables/31.txt'), False)
        self.assertEqual(lfs.exists('fables/broken.txt'), False)


    def test_remove_add(self):
        fables = self.root
        # Firstly add 31.txt
        fables.set_handler('31.txt', TextFile())
        self.database.save_changes()

        fables.del_handler('31.txt')
        fables.set_handler('31.txt', TextFile())
        self.assertEqual(fables.has_handler('31.txt'), True)
        # Save
        self.database.save_changes()
        self.assertEqual(lfs.exists('fables/31.txt'), True)
        self.assertEqual(fables.has_handler('31.txt'), True)


    def test_dot_git(self):
        fables = self.root
        self.assertRaises(ValueError, fables.del_handler, '.git')



start_subprocess('fables')
if __name__ == '__main__':
    main()
