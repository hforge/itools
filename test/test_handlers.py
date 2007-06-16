# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Luis A. Belmar Letelier <luis@itaapy.com>
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
from itools.handlers import get_handler, Python



class FolderTestCase(TestCase):

    def test_has_handler(self):
        handler = get_handler('tests')
        self.assertEqual(handler.has_handler('hello.txt'), True)
       


class TextTestCase(TestCase):
    
    def test_load_file(self):
        handler = get_handler('tests/hello.txt')
        self.assertEqual(handler.data, u'hello world\n')



#    def test_save_file(self):
#        handler = get_handler('tests/hello.txt')
#        handler.data = u'bye world'
#        self.assertEqual(handler.data, u'hello world\n')



#class BasicTestCase(TestCase):

#    def test_get(self):
#        handler = get_handler('hello.txt')
#        self.assertEqual(handler.to_str(), 'hello world\n')


#    def test_copy_file(self):
#        handler = get_handler('hello.txt')
#        copy = handler.copy_handler()
#        self.assertEqual(copy.to_str(), handler.to_str())


#    def test_copy_folder(self):
#        here = get_handler('.')
#        copy = here.copy_handler()
#        self.assertEqual(copy.get_handler('hello.txt').to_str(),
#                         here.get_handler('hello.txt').to_str())





if __name__ == '__main__':
    unittest.main()
