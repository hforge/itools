# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from datetime import datetime
import unittest
from unittest import TestCase

# Import from itools
from itools import vfs
from itools.vfs import APPEND, WRITE
from itools.vfs.file import FileFS
from itools.vfs.registry import get_file_system



class FileTestCase(TestCase):
    """Test the whole API for the filesystem layer, "file://..."
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
        file = vfs.make_file('tests/toto.txt')
        try:
            file.write('hello\n')
        finally:
            file.close()
        # Test
        file = vfs.open('tests/toto.txt', APPEND)
        try:
            file.write('bye\n')
        finally:
            file.close()
        self.assertEqual(open('tests/toto.txt').read(), 'hello\nbye\n')
        # Remove temporary file
        vfs.remove('tests/toto.txt')


    def test21_write_and_truncate(self):
        # Initialize
        file = vfs.make_file('tests/toto.txt')
        try:
            file.write('hello\n')
        finally:
            file.close()
        # Test
        file = vfs.open('tests/toto.txt', WRITE)
        try:
            file.write('bye\n')
        finally:
            file.close()
        self.assertEqual(open('tests/toto.txt').read(), 'bye\n')
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
        vfs.make_folder('tests/toto.txt')


    def tearDown(self):
        if vfs.exists('tests/toto.txt'):
            vfs.remove('tests/toto.txt')


    def test_exists(self):
        exists = self.tests.exists('index.html.en')
        self.assertEqual(exists, True)


    def test_mimetype(self):
        mimetype = vfs.get_mimetype('tests/toto.txt')
        self.assertEqual(mimetype, 'application/x-not-regular-file')



class CopyTestCase(TestCase):

    def setUp(self):
        vfs.make_folder('tmp')


    def tearDown(self):
        if vfs.exists('tmp'):
            vfs.remove('tmp')


    def test_copy_file(self):
        vfs.copy('tests/hello.txt', 'tmp/hello.txt.bak')
        file = vfs.open('tmp/hello.txt.bak')
        try:
            self.assertEqual(file.read(), 'hello world\n')
        finally:
            file.close()


    def test_copy_file_to_folder(self):
        vfs.copy('tests/hello.txt', 'tmp')
        file = vfs.open('tmp/hello.txt')
        try:
            self.assertEqual(file.read(), 'hello world\n')
        finally:
            file.close()


    def test_copy_folder(self):
        vfs.copy('tests', 'tmp/xxx')
        file = vfs.open('tmp/xxx/hello.txt')
        try:
            self.assertEqual(file.read(), 'hello world\n')
        finally:
            file.close()


    def test_copy_folder_to_folder(self):
        vfs.copy('tests', 'tmp')
        file = vfs.open('tmp/tests/hello.txt')
        try:
            self.assertEqual(file.read(), 'hello world\n')
        finally:
            file.close()



class MemFSTestCase(TestCase):
    """
    Test the whole API for the filesystem layer, "mem://..."
    """

    def setUp(self):
        vfs.make_folder('mem:tmp')
        fh = vfs.make_file('mem:tmp/blah.txt')
        fh.write("BLAH!!!")
        fh.close()


    def tearDown(self):
        if vfs.exists('mem:tmp'):
            vfs.remove('mem:tmp')


    def test00_existence(self):
        exists = vfs.exists('mem:fdsfsf')
        self.assertEqual(exists, False)

        # All the following should be synonyms
        exists = vfs.exists('mem:tmp')
        self.assertEqual(exists, True)
        exists = vfs.exists('mem://tmp')
        self.assertEqual(exists, True)
        exists = vfs.exists('mem:///tmp')
        self.assertEqual(exists, True)


    def test01_type_checking(self):
        is_file = vfs.is_file('mem:tmp/blah.txt')
        self.assertEqual(is_file, True)
        is_file = vfs.is_file('mem:tmp')
        self.assertEqual(is_file, False)
        is_folder = vfs.is_folder('mem:tmp')
        self.assertEqual(is_folder, True)
        is_folder = vfs.is_folder('mem:tmp/blah.txt')
        self.assertEqual(is_folder, False)
        mimetype = vfs.get_mimetype('mem:tmp/blah.txt')
        self.assertEqual(mimetype, 'text/plain')


    def test10_creation(self):
        fh = vfs.make_file('mem:testfile.txt')
        fh.write("one\n")
        fh.close()
        self.assertEqual(vfs.is_file('mem:testfile.txt'), True)
        url = 'mem:test/dir'
        vfs.make_folder(url)
        self.assertEqual(vfs.is_folder(url), True)
        url = 'mem:dir1/dir2/dir3/file1'
        fh = vfs.make_file(url)
        fh.write("this is file1")
        fh.close()
        self.assertEqual(vfs.is_file(url), True)

        # this should raise an OSError because it's trying to make a file out
        # of an existing folder
        url = 'mem:dir1/dir2/dir3'
        self.assertRaises(OSError, vfs.make_file, url)

        # this should raise an OSError because it's trying to make a file in
        # another file
        url = 'mem:dir1/dir2/dir3/file1/file2'
        self.assertRaises(OSError, vfs.make_file, url)


    def test11_reading(self):
        fh = vfs.open('mem:testfile.txt')
        self.assertEqual(fh.read(), 'one\n')


    def test12_append(self):
        fh = vfs.open('mem:testfile.txt', vfs.APPEND)
        fh.write("two\n")
        fh.close()
        fh = vfs.open('mem:testfile.txt')
        self.assertEqual(fh.read(), 'one\ntwo\n')
        fh = vfs.open('mem:testfile.txt', vfs.WRITE)
        fh.write("three\n")
        fh.close()
        fh = vfs.open('mem:testfile.txt')
        self.assertEqual(fh.read(), 'three\n')


    def test13_folder_creation(self):
        url = 'mem:testfile.txt/dir'
        self.assertEqual(vfs.is_folder(url), False)
        self.assertRaises(OSError, vfs.make_folder, url)

        # This should raise an OSError because we're trying to make a file
        # inside another file
        fh = vfs.make_file('mem:blah1')
        fh.write("blah1\n")
        fh.close()
        self.assertRaises(OSError, vfs.make_folder, 'mem:blah1/bad1')

        # This should raise OSError because we're trying to make a file with
        # the same name as an existing folder
        url = 'mem:blah2/file2'
        fh = vfs.make_file(url)
        fh.write("blah2\n")
        fh.close()
        self.assertEqual(True, vfs.exists(url))
        self.assertRaises(OSError, vfs.make_file, 'mem:blah2')


    def test20_move_file(self):
        vfs.copy('mem:testfile.txt', 'mem:testfile.txt.bak')
        vfs.move('mem:testfile.txt.bak', 'mem:testfile.txt.old')
        fh = vfs.open('mem:testfile.txt.old')
        self.assertEqual(fh.read(), 'three\n')
        self.assertEqual(vfs.exists('mem:testfile.txt.bak'), False)


    def test21_copy_file(self):
        vfs.copy('tests/hello.txt', 'mem:/tmp/hello.txt')
        fh = vfs.open('mem:/tmp/hello.txt')
        self.assertEqual(fh.read(), 'hello world\n')
        vfs.make_folder('mem:/tmp/folder-test')
        vfs.copy('tests/hello.txt', 'mem:/tmp/folder-test')
        fh = vfs.open('mem:/tmp/folder-test/hello.txt')
        self.assertEqual(fh.read(), 'hello world\n')


    def test22_copy_folder(self):
        vfs.copy('tests', 'mem:/tmp/folder-copy')
        fh = vfs.open('mem:/tmp/folder-copy/hello.txt')
        self.assertEqual(fh.read(), 'hello world\n')
        vfs.make_folder('mem:/tmp/folder-dest')
        vfs.copy('tests', 'mem:/tmp/folder-dest')
        fh = vfs.open('mem:/tmp/folder-dest/tests/hello.txt')
        self.assertEqual(fh.read(), 'hello world\n')


    def test29_remove(self):
        url = 'mem:testfile.txt.old'
        vfs.remove(url)
        self.assertEqual(vfs.exists(url), False)
        url = 'mem:test/dir'
        vfs.make_folder(url)
        vfs.remove(url)
        self.assertEqual(vfs.exists(url), False)
        # Create hierarchy
        vfs.make_folder('mem:tests/folder')
        vfs.make_folder('mem:tests/folder/a')
        vfs.make_file('mem:tests/folder/a/hello.txt')
        # Remove and test
        vfs.remove('mem:tests/folder')
        self.assertEqual(vfs.exists('mem:tests/folder'), False)


    def test30_get_names(self):
        self.assertEqual('blah.txt' in vfs.get_names('mem:tmp'), True)


    def test31_traverse(self):
        for x in vfs.traverse('mem:'):
            self.assertEqual(vfs.exists(x), True)



if __name__ == '__main__':
    unittest.main()
