# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.http.cookies import Cookie, CookieDataType, SetCookieDataType
from itools.http.headers import ContentType, ContentDisposition
from itools.http.parsing import (read_token, read_quoted_string,
    read_parameter, read_parameters)



class ParsingTestCase(TestCase):
    """Test basic parsing functions.
    """

    def test_token(self):
        a = 'Hello World'
        b = ('Hello', ' World')
        self.assertEqual(read_token(a), b)


    def test_quoted_string(self):
        a = '"Hello World"'
        b = ('Hello World', '')
        self.assertEqual(read_quoted_string(a), b)


    def test_parameter(self):
        a = 'Part_Number="Rocket_Launcher_0001"'
        b = ('part_number', 'Rocket_Launcher_0001'), ''
        self.assertEqual(read_parameter(a), b)


    def test_parameters(self):
        a = '; Version="1"; Path="/acme"'
        b = {'version': '1', 'path': '/acme'}, ''
        self.assertEqual(read_parameters(a), b)



class StandardHeadersTestCase(TestCase):

    def test_content_type(self):
        a = 'text/html; charset=UTF-8'
        b = 'text/html', {'charset': 'UTF-8'}
        self.assertEqual(ContentType.decode(a), b)


    def test_content_disposition(self):
        a = ('attachment; filename=genome.jpeg;'
             'modification-date="Wed, 12 Feb 1997 16:29:51 -0500"')
        b = ('attachment',
             {'filename': 'genome.jpeg',
              'modification-date': 'Wed, 12 Feb 1997 16:29:51 -0500'})
        self.assertEqual(ContentDisposition.decode(a), b)



class CookieTestCase(TestCase):

    def test_set_cookie_decode_encode_decode(self):
        a = 'Customer="WILE_E_COYOTE"; Path="/acme"'
        b = SetCookieDataType.decode(a)
        c = SetCookieDataType.encode(b)
        d = SetCookieDataType.decode(c)
        self.assertEqual(b, d)


    def test_cookie_decode_encode_decode(self):
        a = 'Customer="WILE_E_COYOTE"; $Path="/acme"'
        b = CookieDataType.decode(a)
        c = CookieDataType.encode(b)
        d = CookieDataType.decode(c)
        self.assertEqual(b, d)


    #######################################################################
    # Netscape Cookies
    # http://wp.netscape.com/newsref/std/cookie_spec.html
    #######################################################################
    def test_example1(self):
        # Client requests a document, and receives in the response:
        a = ('CUSTOMER=WILE_E_COYOTE; path=/; expires=Wednesday,'
             ' 09-Nov-99 23:12:40 GMT')
        b = {'customer': Cookie('WILE_E_COYOTE', path='/',
                                expires='Wednesday, 09-Nov-99 23:12:40 GMT')}
        self.assertEqual(SetCookieDataType.decode(a), b)
        # When client requests a URL in path "/" on this server, it sends:
        a = 'CUSTOMER=WILE_E_COYOTE'
        b = {'customer': Cookie('WILE_E_COYOTE')}
        self.assertEqual(CookieDataType.decode(a), b)
        # Client requests a document, and receives in the response:
        a = 'PART_NUMBER=ROCKET_LAUNCHER_0001; path=/'
        b = {'part_number': Cookie('ROCKET_LAUNCHER_0001', path='/')}
        self.assertEqual(SetCookieDataType.decode(a), b)
        # When client requests a URL in path "/" on this server, it sends:
        a = 'CUSTOMER=WILE_E_COYOTE; PART_NUMBER=ROCKET_LAUNCHER_0001'
        b = {'customer': Cookie('WILE_E_COYOTE'),
             'part_number': Cookie('ROCKET_LAUNCHER_0001')}
        self.assertEqual(CookieDataType.decode(a), b)
        # Client receives:
        a = 'SHIPPING=FEDEX; path=/foo'
        b = {'shipping': Cookie('FEDEX', path='/foo')}
        self.assertEqual(SetCookieDataType.decode(a), b)
        # When client requests a URL in path "/foo" on this server, it sends:
        a = 'CUSTOMER=WILE_E_COYOTE; PART_NUMBER=ROCKET_LAUNCHER_0001; SHIPPING=FEDEX'
        b = {'customer': Cookie('WILE_E_COYOTE'),
             'part_number': Cookie('ROCKET_LAUNCHER_0001'),
             'shipping': Cookie('FEDEX')}
        self.assertEqual(CookieDataType.decode(a), b)


    #######################################################################
    # Netscape Cookies (old style)
    #######################################################################
    def test_google(self):
        cookie = '__utma=148580960.1549592533.1131137049.1200608996.1200962259.202; __qca=1193853942-44919481-52504193; __utmz=148580960.1196124914.184.2.utmccn=(organic)|utmcsr=google|utmctr=lorum+generator|utmcmd=organic; __qcb=689621141; __utmc=148580960; T3CK=TANT%3D1%7CTANO%3D0; __utma=148580960.1549592533.1131137049.1140634832.1140725853.67'

        expected = {
            '__utma': Cookie('148580960.1549592533.1131137049.1200608996.1200962259.202'),
            '__qca': Cookie('1193853942-44919481-52504193'),
            '__utmz': Cookie('148580960.1196124914.184.2.utmccn=(organic)|utmcsr=google|utmctr=lorum+generator|utmcmd=organic'),
            '__qcb': Cookie('689621141'),
            '__utmc': Cookie('148580960'),
            't3ck': Cookie('TANT%3D1%7CTANO%3D0'),
            '__utma': Cookie('148580960.1549592533.1131137049.1140634832.1140725853.67')}

        self.assertEqual(CookieDataType.decode(cookie), expected)


    #######################################################################
    # Common cases
    #######################################################################
    def test_last_is_empty(self):
        cookie = 'areYourCookiesEnabled='
        expected = {'areyourcookiesenabled': Cookie('')}
        self.assertEqual(CookieDataType.decode(cookie), expected)


    def test_ends_with_semicolon(self):
        cookie = 'language="en";'
        expected = {'language': Cookie('en')}
        self.assertEqual(CookieDataType.decode(cookie), expected)


    def test_garbage(self):
        cookie = 'a=1; toto; b=2'
        expected = {'a': Cookie('1'), 'b': Cookie('2')}
        self.assertEqual(CookieDataType.decode(cookie), expected)



if __name__ == '__main__':
    unittest.main()
