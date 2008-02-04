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
        a = 'Customer="WILE_E_COYOTE"; Version="1"; Path="/acme"'
        b = SetCookieDataType.decode(a)
        c = SetCookieDataType.encode(b)
        d = SetCookieDataType.decode(c)
        self.assertEqual(b, d)


    def test_cookie_decode_encode_decode(self):
        a = '$Version="1"; Customer="WILE_E_COYOTE"; $Path="/acme"'
        b = CookieDataType.decode(a)
        c = CookieDataType.encode(b)
        d = CookieDataType.decode(c)
        self.assertEqual(b, d)


    #######################################################################
    # RFC 2109 Section 5.1 (Example 1)
    #######################################################################
    def test_example1_2(self):
        a = 'Customer="WILE_E_COYOTE"; Version="1"; Path="/acme"'
        b = {'customer': Cookie('WILE_E_COYOTE', version='1', path='/acme')}
        self.assertEqual(SetCookieDataType.decode(a), b)


    def test_example1_3(self):
        a = '$Version="1"; Customer="WILE_E_COYOTE"; $Path="/acme"'
        b = {'customer': Cookie('WILE_E_COYOTE', version='1', path='/acme')}
        self.assertEqual(CookieDataType.decode(a), b)


    def test_example1_4(self):
        a = 'Part_Number="Rocket_Launcher_0001"; Version="1"; Path="/acme"'
        b = {'part_number': Cookie('Rocket_Launcher_0001', version='1',
                                   path='/acme')}
        self.assertEqual(SetCookieDataType.decode(a), b)


    def test_example1_5(self):
        a = ('$Version="1"; Customer="WILE_E_COYOTE"; $Path="/acme";'
             'Part_Number="Rocket_Launcher_0001"; $Path="/acme"')
        b = {'customer': Cookie('WILE_E_COYOTE', version='1', path='/acme'),
             'part_number': Cookie('Rocket_Launcher_0001', version='1',
                                   path='/acme')}
        self.assertEqual(CookieDataType.decode(a), b)


    def test_example1_6(self):
        a = 'Shipping="FedEx"; Version="1"; Path="/acme"'
        b = {'shipping': Cookie('FedEx', version='1', path='/acme')}
        self.assertEqual(SetCookieDataType.decode(a), b)


    def test_example1_7(self):
        a = ('$Version="1"; Customer="WILE_E_COYOTE"; $Path="/acme";'
             'Part_Number="Rocket_Launcher_0001"; $Path="/acme";'
             'Shipping="FedEx"; $Path="/acme"')
        b = {'customer': Cookie('WILE_E_COYOTE', version='1', path='/acme'),
             'part_number': Cookie('Rocket_Launcher_0001', version='1',
                            path='/acme'),
             'shipping': Cookie('FedEx', version='1', path='/acme')}
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





if __name__ == '__main__':
    unittest.main()
