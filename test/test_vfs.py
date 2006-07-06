# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import datetime
import unittest
from unittest import TestCase

# Import from itools
from itools import vfs



class FileTestCase(TestCase):
    """
    Test the whole API for the filesystem layer, "file://..."
    """

    def test00_exists(self):
        exists = vfs.exists('tests/index.html.en')
        self.assertEqual(exists, True)


    def test01_does_not_exist(self):
        exists = vfs.exists('tests/fdsfsf')
        self.assertEqual(exists, False)

    
    def test02_is_file(self):
        is_file = vfs.is_file('tests/index.html.en')
        self.assertEqual(is_file, True)


    def test03_is_not_file(self):
        is_file = vfs.is_file('tests')
        self.assertEqual(is_file, False)


    def test04_is_folder(self):
        is_folder = vfs.is_folder('tests')
        self.assertEqual(is_folder, True)


    def test05_is_not_folder(self):
        is_folder = vfs.is_file('tests/index.html.en')
        self.assertEqual(is_folder, True)


    def test06_make_file(self):
        vfs.make_file('tests/file')
        self.assertEqual(vfs.is_file('tests/file'), True)


    def test07_make_folder(self):
        vfs.make_folder('tests/folder')
        self.assertEqual(vfs.is_folder('tests/folder'), True)


    def test08_ctime(self):
        ctime = vfs.get_ctime('tests/file')
        self.assertEqual(ctime.year, datetime.now().year)


    def test09_mtime(self):
        mtime = vfs.get_mtime('tests/file')
        self.assertEqual(mtime.year, datetime.now().year)


    def test10_atime(self):
        atime = vfs.get_atime('tests/file')
        self.assertEqual(atime.year, datetime.now().year)


    def test11_get_mimetype(self):
        mimetype = vfs.get_mimetype('tests/hello.txt')
        self.assertEqual(mimetype, 'text/plain')


    def test12_remove_file(self):
        vfs.remove('tests/file')
        self.assertEqual(vfs.exists('tests/file'), False)


    def test13_remove_empty_folder(self):
        vfs.remove('tests/folder')
        self.assertEqual(vfs.exists('tests/folder'), False)


    def test14_remove_folder(self):
        # Create hierarchy
        vfs.make_folder('tests/folder')
        vfs.make_folder('tests/folder/a')
        vfs.make_file('tests/folder/a/hello.txt')
        # Remove and test
        vfs.remove('tests/folder')
        self.assertEqual(vfs.exists('tests/folder'), False)


    def test15_open_file(self):
        file = vfs.open('tests/hello.txt')
        self.assertEqual(file.read(), 'hello world\n')


#    def test16_open_file(self):


    def test17_copy_file(self):
        vfs.copy('tests/hello.txt', 'tests/hello.txt.bak')
        file = vfs.open('tests/hello.txt.bak')
        self.assertEqual(file.read(), 'hello world\n')


    def test18_move_file(self):
        vfs.move('tests/hello.txt.bak', 'tests/hello.txt.old')
        file = vfs.open('tests/hello.txt.old')
        self.assertEqual(file.read(), 'hello world\n')
        self.assertEqual(vfs.exists('tests/hello.txt.bak'), False)


    def test19_get_names(self):
        self.assertEqual('hello.txt.old' in vfs.get_names('tests'), True)
        # Remove temporary file
        vfs.remove('tests/hello.txt.old')



class FoldersTestCase(TestCase):
 
    def setUp(self):
        self.tests = vfs.open('tests/')


    def test00_exists(self):
        exists = self.tests.exists('index.html.en')
        self.assertEqual(exists, True)





if __name__ == '__main__':
    unittest.main()
