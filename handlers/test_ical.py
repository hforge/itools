# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from Python
import unittest
from unittest import TestCase

# Import from itools
import iCalendar as ical


class UnfoldTestCase(TestCase):
    def test(self):
        data = 'DESCRIPTION:This is a lo\r\n' \
               ' ng description\r\n' \
               '  that exists on a long line.'
        lines = list(ical.get_lines(data))
        expect = 'DESCRIPTION:This is a long description that exists' \
                 ' on a long line.'
        self.assertEqual(lines, [expect])


class ParametersTestCase(TestCase):
    def test(self):
        data = 'name;p1=v1;p2="v21;:v22":value'
        params = list(ical.parse_line(data))
        expect = [(ical.NAME, 'name'),
                  (ical.PNAME, 'p1'), (ical.PVALUE, 'v1'),
                  (ical.PNAME, 'p2'), (ical.PVALUE, 'v21;:v22'),
                  (ical.VALUE, 'value')]
        self.assertEqual(params, expect)



if __name__ == '__main__':
    unittest.main()
