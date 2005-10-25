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
        """A path equals the same with a trailing slash."""
        self.assertEqual(self.path_wo_slash, self.path_w_slash)


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


if __name__ == '__main__':
    unittest.main()
