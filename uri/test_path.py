# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import unittest

# Import from itools
from generic import Path


class PathComparisonTestCase(unittest.TestCase):

    def setUp(self):
        self.path_wo_slash = Path('/a/b/c')
        self.path_w_slash = Path('/a/b/c/')
        self.wo_to_w = self.path_wo_slash.get_pathto(self.path_w_slash)


    #
    # Comparing Path objects
    #

    def test_with_eq_without_trailing_slash(self):
        """A path is not the same with a trailing slash."""
        self.assertNotEqual(self.path_wo_slash, self.path_w_slash)


    def test_wo_to_w_eq_path_dot(self):
        """The path to the same with a trailing slash returns Path('.')."""
        self.assertEqual(self.wo_to_w, Path('.'))

    
    #
    # Comparing with string conversions.
    #

    def test_path_wo_slash_eq_string(self):
        """A path without trailing slash equals its string conversion."""
        self.assertEqual(self.path_wo_slash, str(self.path_wo_slash))


    def test_path_w_slash_eq_string(self):
        """A path with trailing slash equals its string conversion."""
        self.assertEqual(self.path_w_slash, str(self.path_w_slash))


    def test_path_to_similar_eq_string_dot(self):
        """The path to the same with a trailing slash equals '.'."""
        self.assertEqual(self.wo_to_w, '.')



class PathResolveTestCase(unittest.TestCase):

    def test_resolve_wo_slash(self):
        before = Path('/a/b')
        after = Path('/a/c')
        self.assertEqual(before.resolve('c'), after)


    def test_resolve_w_slash(self):
        before = Path('/a/b/')
        after = Path('/a/b/c')
        self.assertEqual(before.resolve('c'), after)


class PathResolve2TestCase(unittest.TestCase):

    def test_resolve2_wo_slash(self):
        before = Path('/a/b')
        after = Path('/a/b/c')
        self.assertEqual(before.resolve2('c'), after)


    def test_resolve2_w_slash(self):
        before = Path('/a/b/')
        after = Path('/a/b/c')
        self.assertEqual(before.resolve2('c'), after)


class PathPrefixTestCase(unittest.TestCase):
    # TODO more test cases.

    def test1(self):
        a = Path('/a/b/c')
        b = Path('/a/b/d/e')
        self.assertEqual(a.get_prefix(b), 'a/b')


class PathPathToTestCase(unittest.TestCase):

    def test_pathto_wo_slash(self):
        before = Path('/a/b')
        after = Path('/a/b/c')
        self.assertEqual(before.get_pathto(after), 'c')


    def test_pathto_w_slash(self):
        before = Path('/a/b/')
        after = Path('/a/b/c')
        self.assertEqual(before.get_pathto(after), 'c')


class PathPathToRootTestCase(unittest.TestCase):

    def test1(self):
        a = Path('/a')
        self.assertEqual(a.get_pathtoroot(), '')


    def test2(self):
        a = Path('/a/')
        self.assertEqual(a.get_pathtoroot(), '')


    def test3(self):
        a = Path('/a/b')
        self.assertEqual(a.get_pathtoroot(), '../')


    def test4(self):
        a = Path('/a/b/')
        self.assertEqual(a.get_pathtoroot(), '../')


    def test5(self):
        a = Path('/a/very/long/path')
        self.assertEqual(a.get_pathtoroot(), '../../../')


    def test6(self):
        a = Path('a/b')
        self.assertEqual(a.get_pathtoroot(), '../')


    def test7(self):
        a = Path('a/b/')
        self.assertEqual(a.get_pathtoroot(), '../')


if __name__ == '__main__':
    unittest.main()
