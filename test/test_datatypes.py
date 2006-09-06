# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Nicolas Deram <nderam@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from datetime import time
import unittest
from unittest import TestCase

# Import from itools
from itools.datatypes import Time


class DatatypesTestCase(TestCase):

    def test_time_decode(self):
        data = '13:45:30'
        value = Time.decode(data)
        expected = time(13, 45, 30)
        self.assertEqual(value, expected)

        data = '13:45'
        value = Time.decode(data)
        expected = time(13, 45)
        self.assertEqual(value, expected)


    def test_time_encode(self):
        data = time(13, 45, 30)
        value = Time.encode(data)
        expected = '13:45:30'
        self.assertEqual(value, expected)

        data = time(13, 45)
        value = Time.encode(data)
        expected = '13:45:00'
        self.assertEqual(value, expected)

        data = time(13, 45)
        value = Time.encode(data, False)
        expected = '13:45'
        self.assertEqual(value, expected)



if __name__ == '__main__':
    unittest.main()
