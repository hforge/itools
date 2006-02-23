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
from unittest import TestCase

# Import from itools
import generic


class PathTestCase(TestCase):

    def test_simplenorm(self):
        """
        Test the simple path normalization:

        - 'a/./b' = 'a/b'
        - 'a//b'  = 'a/b'
        - './a'   = 'a'
        - 'a/'    = 'a'
        """
        path = generic.Path('./a/./b//c/')
        self.assertEqual(str(path), 'a/b/c/')


    def test_backnorm(self):
        """
        Test the normalization 'a/../b' = 'b'
        """
        path = generic.Path('a/b/c/../d')
        self.assertEqual(str(path), 'a/b/d')


    def test_absnorm(self):
        """
        Test the normalization '/..' = '/'
        """
        path = generic.Path('/../../a/b/c')
        self.assertEqual(str(path), '/a/b/c')


    def test_relnorm(self):
        """
        Check that '../' = '../'
        """
        path = generic.Path('../../a//.//b/c')
        self.assertEqual(str(path), '../../a/b/c')



class ParseTestCase(TestCase):
    """
    Tests to verify the correct parsing of generic references.
    """

    def test_full(self):
        ref = 'http://example.com/a/b/c?query#fragment'
        ref = generic.decode(ref)
        self.assertEqual(ref.scheme, 'http')
        self.assertEqual(ref.authority, 'example.com')
        self.assertEqual(ref.path, '/a/b/c')
        self.assertEqual(ref.query, 'query')
        self.assertEqual(ref.fragment, 'fragment')


    def test_network(self):
        ref = '//example.com/a/b'
        ref = generic.decode(ref)
        self.assertEqual(bool(ref.scheme), False)
        self.assertEqual(ref.authority, 'example.com')
        self.assertEqual(ref.path, '/a/b')


    def test_path(self):
        ref = '/a/b/c'
        ref = generic.decode(ref)
        self.assertEqual(bool(ref.scheme), False)
        self.assertEqual(bool(ref.authority), False)
        self.assertEqual(ref.path, '/a/b/c')


    def test_query(self):
        ref = '?query'
        ref = generic.decode(ref)
        self.assertEqual(bool(ref.scheme), False)
        self.assertEqual(bool(ref.authority), False)
        self.assertEqual(len(ref.path), 0)
        self.assertEqual(ref.query, 'query')


class SpecialTestCase(TestCase):
    """Test special cases."""

    def test_fragment(self):
        self.assertEqual(str(generic.decode('#')), '#')


    def test_dot(self):
        self.assertEqual(str(generic.decode('.')), '.')


    def test_empty(self):
        self.assertEqual(str(generic.decode('')), '')



class ResolveTestCase(TestCase):
    """
    This test case comes from the appendix C of the RFC2396.
    """

    def setUp(self):
        self.base = generic.decode('http://a/b/c/d;p?q')


    def test_standard(self):
        # Test the cases defined by RFC2396, section C.1
        failure = 0
        for reference, expected in [('g:h', 'g:h'),
                                    ('g', 'http://a/b/c/g'),
                                    ('./g', 'http://a/b/c/g'),
                                    ('g/', 'http://a/b/c/g/'),
                                    ('/g', 'http://a/g'),
                                    ('//g', 'http://g'),
                                    ('?y', 'http://a/b/c/?y'),
                                    ('g?y', 'http://a/b/c/g?y'),
                                    ('#s', 'http://a/b/c/d;p?q#s'),
                                    ('g#s', 'http://a/b/c/g#s'),
                                    ('g?y#s', 'http://a/b/c/g?y#s'),
                                    (';x', 'http://a/b/c/;x'),
                                    ('g;x', 'http://a/b/c/g;x'),
                                    ('g;x?y#s', 'http://a/b/c/g;x?y#s'),
                                    ('.', 'http://a/b/c/'),
                                    ('./', 'http://a/b/c/'),
                                    ('..', 'http://a/b/'),
                                    ('../', 'http://a/b/'),
                                    ('../g', 'http://a/b/g'),
                                    ('../..', 'http://a/'),
                                    ('../../', 'http://a/'),
                                    ('../../g', 'http://a/g')]:
            x = self.base.resolve(reference)
            try:
                self.assertEqual(x, expected)
            except AssertionError:
                print '\n%s + %s = %s != %s' \
                      % (self.base, reference, x, expected)
                failure += 1
        if failure:
            raise AssertionError, '%s uri resolutions failed' % failure


    def test_others(self):
        self.assertEqual(self.base.resolve(''), 'http://a/b/c/d;p?q')



if __name__ == '__main__':
    unittest.main()
