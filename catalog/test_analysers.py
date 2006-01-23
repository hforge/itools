# -*- coding: UTF-8 -*-
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
import unittest
from unittest import TestCase

# Import from itools
import analysers


class TextTestCase(TestCase):

    def test_hello(self):
        words = list(analysers.Text(u'Hello world'))
        self.assertEqual(words, [(u'hello', 0), (u'world', 1)])


    def test_accents(self):
        words = list(analysers.Text(u'Te doy una canción'))
        self.assertEqual(words, [(u'te', 0), (u'doy', 1), (u'una', 2),
                                 (u'canción', 3)])


    def test_russian(self):
        text = u'Это наш дом'
        words = list(analysers.Text(text))
        self.assertEqual(words, [(u'это', 0), (u'наш', 1),  (u'дом', 2)])



if __name__ == '__main__':
    unittest.main()
