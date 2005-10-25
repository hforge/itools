# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from the Standard Library
import unittest

# Import from itools
from generic import normalize_path


class PathNormalizeTestCase(unittest.TestCase):
    """These tests come from the uri.generic.normalize_path docstring."""

    def test1(self):
        """'a//b/c' -> 'a/b/c'"""
        self.assertEqual(normalize_path('a//b/c'), 'a/b/c')


    def test2(self):
        """'a/./b/c' -> 'a/b/c'"""
        self.assertEqual(normalize_path('a/./b/c'), 'a/b/c')


    def test3(self):
        """'a/b/c/../d' -> 'a/b/d'"""
        self.assertEqual(normalize_path('a/b/c/../d'), 'a/b/d')


    def test4(self):
        """'/../a/b/c' -> 'a/b/c'"""
        self.assertEqual(normalize_path('/../a/b/c'), '/a/b/c')


    def test_dot(self):
        """'.' -> ''"""
        self.assertEqual(normalize_path('.'), '')


if __name__ == '__main__':
    unittest.main()
