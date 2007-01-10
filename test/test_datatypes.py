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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
from datetime import time
import unittest
from unittest import TestCase

# Import from itools
from itools.datatypes import ISOTime, InternetDateTime


class ISOTimeTestCase(TestCase):

    def test_time_decode(self):
        data = '13:45:30'
        value = ISOTime.decode(data)
        expected = time(13, 45, 30)
        self.assertEqual(value, expected)

        data = '13:45'
        value = ISOTime.decode(data)
        expected = time(13, 45)
        self.assertEqual(value, expected)


    def test_time_encode(self):
        data = time(13, 45, 30)
        value = ISOTime.encode(data)
        expected = '13:45:30'
        self.assertEqual(value, expected)

        data = time(13, 45)
        value = ISOTime.encode(data)
        expected = '13:45:00'
        self.assertEqual(value, expected)

        data = time(13, 45)
        value = ISOTime.encode(data)
        expected = '13:45:00'
        self.assertEqual(value, expected)



class InternetDateTimeTestCase(TestCase):

    def test_datetime(self):
        test_dates = {
            'Tue, 14 Jun 2005 09:00:00 -0400': '2005-06-14 13:00:00',
            'Tue, 14 Jun 2005 09:00:00 +0200': '2005-06-14 07:00:00',
            'Thu, 28 Jul 2005 15:36:55 EDT': '2005-07-28 19:36:55',
            'Fri, 29 Jul 2005 05:50:13 GMT': '2005-07-29 05:50:13',
            '29 Jul 2005 07:27:19 UTC': '2005-07-29 07:27:19',
            '02 Jul 2005 09:52:23 GMT': '2005-07-02 09:52:23'
        }
        for dt, utc in test_dates.items():
            d = InternetDateTime.decode(dt)
            self.assertEqual(InternetDateTime.encode(d), utc)





if __name__ == '__main__':
    unittest.main()
