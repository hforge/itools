# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import datetime
import unittest
from unittest import TestCase

# Import from itools
from itools.web.headers import HTTPDate


class DateTestCase(TestCase):

    def test_rfc822(self):
        date = 'Sun, 06 Nov 1994 08:49:37 GMT'
        date = HTTPDate.decode(date)
        self.assertEqual(date, datetime(1994, 11, 6, 8, 49, 37))


    def test_rfc850(self):
        date = 'Sunday, 06-Nov-94 08:49:37 GMT'
        date = HTTPDate.decode(date)
        self.assertEqual(date, datetime(1994, 11, 6, 8, 49, 37))


    def test_asctime(self):
        date = 'Sun Nov  6 08:49:37 1994'
        date = HTTPDate.decode(date)
        self.assertEqual(date, datetime(1994, 11, 6, 8, 49, 37))


    def test_encode(self):
        date = datetime(1994, 11, 6, 8, 49, 37)
        date = HTTPDate.encode(date)
        self.assertEqual(date, 'Sun, 06 Nov 1994 08:49:37 GMT')


if __name__ == '__main__':
    unittest.main()
