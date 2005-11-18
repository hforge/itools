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
import unittest
from unittest import TestCase

# Import from itools
import IO


class IOTestCase(TestCase):

    def test_byte(self):
        value = 27
        encoded_value = IO.encode_byte(value)
        self.assertEqual(IO.decode_byte(encoded_value), value)


    def test_unit32(self):
        value = 1234
        encoded_value = IO.encode_uint32(value)
        self.assertEqual(IO.decode_uint32(encoded_value), value)


    def test_vint(self):
        value = 1234567890
        encoded_value = IO.encode_vint(value)
        self.assertEqual(IO.decode_vint(encoded_value)[0], value)


    def test_character(self):
        value = u'X'
        encoded_value = IO.encode_character(value)
        self.assertEqual(IO.decode_character(encoded_value), value)


    def test_string(self):
        value = u'aquilas non captis muscas'
        encoded_value = IO.encode_string(value)
        self.assertEqual(IO.decode_string(encoded_value)[0], value)


    def test_link(self):
        for value in [0, 513]:
            encoded_value = IO.encode_link(value)
            self.assertEqual(IO.decode_link(encoded_value), value)


    def test_varsion(self):
        value = '20050217'
        encoded_value = IO.encode_version(value)
        self.assertEqual(IO.decode_version(encoded_value), value)



if __name__ == '__main__':
    unittest.main()
