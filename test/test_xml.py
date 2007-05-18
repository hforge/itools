# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.xml import (Document, Parser, XMLError, XML_DECL, DOCUMENT_TYPE,
                        START_ELEMENT, END_ELEMENT, TEXT, COMMENT, PI, CDATA)



class ParserTestCase(TestCase):

    def test_xml_decl(self):
        data = '<?xml version="1.0" encoding="UTF-8"?>'
        token = XML_DECL
        value = '1.0', 'UTF-8', None
        self.assertEqual(Parser(data).next(), (token, value, 1))


    #######################################################################
    # Character References
    def test_char_ref(self):
        data = '&#241;'
        token = TEXT
        value = "ñ"
        self.assertEqual(Parser(data).next(), (token, value, 1))


    def test_char_ref_hex(self):
        data = '&#xf1;'
        token = TEXT
        value = "ñ"
        self.assertEqual(Parser(data).next(), (token, value, 1))


    def test_char_ref_empty(self):
        data = '&#;'
        self.assertRaises(XMLError, Parser(data).next)


    #######################################################################
    # Start Element
    def test_element(self):
        data = '<a>'
        token = START_ELEMENT
        value = None, 'a', {}
        self.assertEqual(Parser(data).next(), (token, value, 1))


    def test_attributes(self):
        data = '<a href="http://www.ikaaro.org">'
        token = START_ELEMENT
        value = None, 'a', {(None, 'href'): 'http://www.ikaaro.org'}
        self.assertEqual(Parser(data).next(), (token, value, 1))


    def test_attributes_single_quote(self):
        data = "<a href='http://www.ikaaro.org'>"
        token = START_ELEMENT
        value = None, 'a', {(None, 'href'): 'http://www.ikaaro.org'}
        self.assertEqual(Parser(data).next(), (token, value, 1))


    def test_attributes_no_quote(self):
        data = "<a href=http://www.ikaaro.org>"
        self.assertRaises(XMLError, Parser(data).next)


    def test_attributes_forbidden_char(self):
        data = '<img title="Black & White">'
        self.assertRaises(XMLError, Parser(data).next)


    def test_attributes_entity_reference(self):
        data = '<img title="Black &amp; White">'
        token = START_ELEMENT
        value = None, 'img', {(None, 'title'): 'Black & White'}
        self.assertEqual(Parser(data).next(), (token, value, 1))


    #######################################################################
    # CDATA
    def test_cdata(self):
        data = '<![CDATA[Black & White]]>'
        token = CDATA
        value = 'Black & White'
        self.assertEqual(Parser(data).next(), (token, value, 1))


class XMLTestCase(TestCase):

    def test_identity(self):
        """
        Tests wether the input and the output match.
        """
        data = '<html>\n' \
               '<head></head>\n' \
               '<body>\n' \
               ' this is a <span style="color: red">test</span>\n' \
               '</body>\n' \
               '</html>'
        h1 = Document(string=data)
        h2 = Document(string=data)

        self.assertEqual(h1, h2)



if __name__ == '__main__':
    unittest.main()
