# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
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
from unittest import TestCase, main

# Import from itools
from itools import vfs
from itools.vfs import APPEND, WRITE, FileName


class DatatypesTestCase(TestCase):

    def test_FileName(self):
        map = {
            'index': ('index', None, None),
            'index.html': ('index', 'html', None),
            'index.html.en': ('index', 'html', 'en'),
            'index.html.en.gz': ('index.html.en', 'gz', None),
            'itools.tar': ('itools', 'tar', None),
            'itools.tar.gz': ('itools.tar', 'gz', None),
            'toto.en': ('toto', None, 'en'),
            'toto.gz': ('toto', 'gz', None),
            'toto.Z': ('toto', 'Z', None),
            }
        for name, result in map.iteritems():
            self.assertEqual(FileName.decode(name), result)
            self.assertEqual(FileName.encode(result), name)



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



class MimeTestCase(TestCase):

    def test_archive(self):
        # FIXME Compression schemes are not mimetypes, see /etc/mime.types
        mimetype = vfs.get_mimetype('handlers/test.tar.gz')
        self.assertEqual(mimetype, 'application/x-tgz')


if __name__ == '__main__':
    main()
