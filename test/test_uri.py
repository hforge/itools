# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 Rob McMullen <rob.mcmullen@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools
from itools.uri import get_reference, Path, Reference
from itools.uri.generic import normalize_path, GenericDataType
from itools.uri.mailto import Mailto, MailtoDataType



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



class PathComparisonTestCase(unittest.TestCase):

    def setUp(self):
        self.path_wo_slash = Path('/a/b/c')
        self.path_w_slash = Path('/a/b/c/')
        self.wo_to_w = self.path_wo_slash.get_pathto(self.path_w_slash)


    #########################################################################
    # Comparing Path objects
    def test_with_eq_without_trailing_slash(self):
        """A path is not the same with a trailing slash."""
        self.assertNotEqual(self.path_wo_slash, self.path_w_slash)


    def test_wo_to_w_eq_path_dot(self):
        """The path to the same with a trailing slash returns Path('.')."""
        self.assertEqual(self.wo_to_w, Path('.'))


    #########################################################################
    # Comparing with string conversions.
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
        self.assertEqual(a.get_prefix(b), '/a/b')



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



class PathTestCase(TestCase):

    def test_simplenorm(self):
        """
        Test the simple path normalization:

        - 'a/./b' = 'a/b'
        - 'a//b'  = 'a/b'
        - './a'   = 'a'
        - 'a/'    = 'a'
        """
        path = Path('./a/./b//c/')
        self.assertEqual(str(path), 'a/b/c/')


    def test_backnorm(self):
        """
        Test the normalization 'a/../b' = 'b'
        """
        path = Path('a/b/c/../d')
        self.assertEqual(str(path), 'a/b/d')


    def test_absnorm(self):
        """
        Test the normalization '/..' = '/'
        """
        path = Path('/../../a/b/c')
        self.assertEqual(str(path), '/a/b/c')


    def test_relnorm(self):
        """
        Check that '../' = '../'
        """
        path = Path('../../a//.//b/c')
        self.assertEqual(str(path), '../../a/b/c')



class ParseTestCase(TestCase):
    """
    Tests to verify the correct parsing of generic references.
    """

    def test_full(self):
        ref = 'http://example.com/a/b/c?query#fragment'
        ref = GenericDataType.decode(ref)
        self.assertEqual(ref.scheme, 'http')
        self.assertEqual(ref.authority, 'example.com')
        self.assertEqual(ref.path, '/a/b/c')
        self.assertEqual(ref.query, {'query': None})
        self.assertEqual(ref.fragment, 'fragment')


    def test_network(self):
        ref = '//example.com/a/b'
        ref = GenericDataType.decode(ref)
        self.assertEqual(bool(ref.scheme), False)
        self.assertEqual(ref.authority, 'example.com')
        self.assertEqual(ref.path, '/a/b')


    def test_path(self):
        ref = '/a/b/c'
        ref = GenericDataType.decode(ref)
        self.assertEqual(bool(ref.scheme), False)
        self.assertEqual(bool(ref.authority), False)
        self.assertEqual(ref.path, '/a/b/c')


    def test_query(self):
        ref = '?query'
        ref = GenericDataType.decode(ref)
        self.assertEqual(bool(ref.scheme), False)
        self.assertEqual(bool(ref.authority), False)
        self.assertEqual(len(ref.path), 0)
        self.assertEqual(ref.query, {'query': None})


    def test_windows_normalize(self):
        uri = GenericDataType.decode('c:stuff/blah')
        self.assertEqual('c:stuff/blah', uri.path)
        self.assertEqual('file', uri.scheme)
        uri = GenericDataType.decode('file:///c:/stuff/blah')
        self.assertEqual('c:/stuff/blah', uri.path)
        self.assertEqual('file', uri.scheme)
        uri = GenericDataType.decode('C:/stuff/blah')
        self.assertEqual('c:/stuff/blah', uri.path)
        self.assertEqual('file', uri.scheme)



class SpecialTestCase(TestCase):
    """Test special cases."""

    def test_fragment(self):
        self.assertEqual(str(GenericDataType.decode('#')), '#')


    def test_dot(self):
        self.assertEqual(str(GenericDataType.decode('.')), '.')


    def test_empty(self):
        self.assertEqual(str(GenericDataType.decode('')), '')



class ResolveTestCase(TestCase):
    """
    This test case comes from the appendix C of the RFC2396.
    """

    def setUp(self):
        self.base = GenericDataType.decode('http://a/b/c/d;p?q')


    def test_standard(self):
        # Test Cases defined by RFC2396, section C.1
        cases = [
            ('gg:h', 'gg:h'),  # NOTE This is a little different
            ('g', 'http://a/b/c/g'),
            ('./g', 'http://a/b/c/g'),
            ('g/', 'http://a/b/c/g/'),
            ('/g', 'http://a/g'),
# FIXME     ('//g', 'http://g'),
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
# FIXME     ('..', 'http://a/b/'),
            ('../', 'http://a/b/'),
            ('../g', 'http://a/b/g'),
            ('../..', 'http://a/'),
            ('../../', 'http://a/'),
            ('../../g', 'http://a/g')]
        # Test
        failure = 0
        for reference, expected in cases:
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



class ReferenceTestCase(unittest.TestCase):

    def test_mailto(self):
        """Test if mailto references are detected."""
        ref = get_reference('mailto:jdavid@itaapy.com')
        self.assert_(isinstance(ref, Mailto))


    def test_http(self):
        """http references are generic."""
        ref = get_reference('http://ikaaro.org')
        self.assert_(isinstance(ref, Reference))


    def test_ftp(self):
        """references with unknow scheme are generic."""
        ref = get_reference('http://ikaaro.org')
        self.assert_(isinstance(ref, Reference))


    def test_no_scheme(self):
        """references with no scheme are generic."""
        ref = get_reference('logo.png')
        self.assert_(isinstance(ref, Reference))



class MailtoTestCase(unittest.TestCase):

    def setUp(self):
        self.username = 'jdavid'
        self.host = 'itaapy.com'
        self.address = 'jdavid@itaapy.com'
        self.uri = 'mailto:jdavid@itaapy.com'
        self.uri_no_host = 'mailto:jdavid'


    def test_mailto(self):
        """Regular Mailto object."""
        ob = Mailto(self.address)
        self.assertEqual(ob.username, self.username)
        self.assertEqual(ob.host, self.host)
        self.assertEqual(str(ob), self.uri)


    def test_mailto_no_host(self):
        """Mailto object with no host."""
        ob = Mailto(self.username)
        self.assertEqual(ob.username, None)
        self.assertEqual(ob.host, None)
        self.assertEqual(str(ob), self.uri_no_host)


    def test_decode(self):
        """Decoding of a regular "mailto:" reference."""
        ob = MailtoDataType.decode(self.uri)
        self.assert_(isinstance(ob, Mailto))
        self.assertEqual(ob.username, self.username)
        self.assertEqual(ob.host, self.host)
        self.assertEqual(str(ob), self.uri)


    def test_decode_no_host(self):
        """Decoding of a "mailto:" reference with no @host."""
        ob = MailtoDataType.decode(self.uri_no_host)
        self.assert_(isinstance(ob, Mailto))
        self.assertEqual(ob.username, None)
        self.assertEqual(ob.host, None)
        self.assertEqual(str(ob), self.uri_no_host)


    def test_compare(self):
        """Compare two Mailto objects with same parameters."""
        ob = Mailto(self.address)
        copy = MailtoDataType.decode(self.uri)
        self.assert_(type(ob) is type(copy))
        self.assertEqual(ob.username, copy.username)
        self.assertEqual(ob.host, copy.host)
        self.assertEqual(str(ob), str(copy))
        self.assertEqual(ob, copy)



if __name__ == '__main__':
    unittest.main()
