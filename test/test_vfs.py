# -*- coding: UTF-8 -*-
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

# Import from the future
from __future__ import with_statement

# Import from the Standard Library
from datetime import datetime
import unittest
from unittest import TestCase

# Import from itools
from itools import vfs
from itools.vfs import APPEND, FileFS
from itools.vfs.registry import get_file_system



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


    def test17_move_file(self):
        vfs.copy('tests/hello.txt', 'tests/hello.txt.bak')
        vfs.move('tests/hello.txt.bak', 'tests/hello.txt.old')
        file = vfs.open('tests/hello.txt.old')
        self.assertEqual(file.read(), 'hello world\n')
        self.assertEqual(vfs.exists('tests/hello.txt.bak'), False)


    def test18_get_names(self):
        self.assertEqual('hello.txt.old' in vfs.get_names('tests'), True)
        # Remove temporary file
        vfs.remove('tests/hello.txt.old')


    def test19_traverse(self):
        for x in vfs.traverse('.'):
            self.assertEqual(vfs.exists(x), True)


    def test20_append(self):
        # Initialize
        with vfs.make_file('tests/toto.txt') as file:
            file.write('hello\n')
        # Test
        with vfs.open('tests/toto.txt', APPEND) as file:
            file.write('bye\n')
        self.assertEqual(open('tests/toto.txt').read(), 'hello\nbye\n')
        # Remove temporary file
        vfs.remove('tests/toto.txt')



class FSTestCase(TestCase):

    def test_linux(self):
        # file://home/toto.txt
        fs = get_file_system('file')
        self.assertEqual(fs, FileFS)


    def test_windows(self):
        # c:\toto.txt
        fs = get_file_system('c')
        self.assertEqual(fs, FileFS)



class FoldersTestCase(TestCase):
 
    def setUp(self):
        self.tests = vfs.open('tests/')


    def test00_exists(self):
        exists = self.tests.exists('index.html.en')
        self.assertEqual(exists, True)



class CopyTestCase(TestCase):

    def setUp(self):
        vfs.make_folder('tmp')


    def tearDown(self):
        if vfs.exists('tmp'):
            vfs.remove('tmp')


    def test_copy_file(self):
        vfs.copy('tests/hello.txt', 'tmp/hello.txt.bak')
        with vfs.open('tmp/hello.txt.bak') as file:
            self.assertEqual(file.read(), 'hello world\n')


    def test_copy_file_to_folder(self):
        vfs.copy('tests/hello.txt', 'tmp')
        with vfs.open('tmp/hello.txt') as file:
            self.assertEqual(file.read(), 'hello world\n')


    def test_copy_folder(self):
        vfs.copy('tests', 'tmp/xxx')
        with vfs.open('tmp/xxx/hello.txt') as file:
            self.assertEqual(file.read(), 'hello world\n')


    def test_copy_folder_to_folder(self):
        vfs.copy('tests', 'tmp')
        with vfs.open('tmp/tests/hello.txt') as file:
            self.assertEqual(file.read(), 'hello world\n')



if __name__ == '__main__':
    unittest.main()
