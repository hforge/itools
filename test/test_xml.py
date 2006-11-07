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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools
from itools.xml import XML
from itools.xml.parser import Parser, XMLError
from itools.xml.parser import XML_DECL, DOCUMENT_TYPE, START_ELEMENT, \
    END_ELEMENT, TEXT, COMMENT, PI, CDATA


#class CParserTestCase(TestCase):

#   def test_xml_decl(self):
#       data = '<?xml version="1.0" encoding="UTF-8"?>'
#       x = Parser(data).get_token()
#       self.assertEqual(x, (XML_DECL, ('1.0', 'UTF-8'), 1))


#   def test_element(self):
#       data = '<a>'
#       x = Parser(data).get_token()
#       self.assertEqual(x, (START_ELEMENT, (None, 'a', {}), 1))



class ParserTestCase(TestCase):

    def test_xml_decl(self):
        data = '<?xml version="1.0" encoding="UTF-8"?>'
        token = XML_DECL
        value = '1.0', 'UTF-8', None
        self.assertEqual(Parser(data).next(), (token, value, 1))


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
        h1 = XML.Document()
        h1.load_state_from_string(data)
        h2 = XML.Document()
        h2.load_state_from_string(data)

        self.assertEqual(h1, h2)



if __name__ == '__main__':
    unittest.main()
