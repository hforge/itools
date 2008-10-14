# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
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
from itools import html
from itools.xml import (XMLFile, XMLParser, DocType, XMLError, XML_DECL,
    DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT, COMMENT, PI, CDATA,
    stream_to_str, get_doctype)
from itools.xml.i18n import get_units
from itools.gettext import POUnit
from itools.srx import TEXT as srx_TEXT


class ParserTestCase(TestCase):

    def test_xml_decl(self):
        data = '<?xml version="1.0" encoding="UTF-8"?>'
        token = XML_DECL
        value = '1.0', 'UTF-8', None
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    #######################################################################
    # Character References
    def test_char_ref(self):
        data = '&#241;'
        token = TEXT
        value = "ñ"
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_char_ref_hex(self):
        data = '&#xf1;'
        token = TEXT
        value = "ñ"
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_char_ref_empty(self):
        data = '&#;'
        self.assertRaises(XMLError, XMLParser(data).next)


    #######################################################################
    # Start Element
    def test_element(self):
        data = '<a>'
        token = START_ELEMENT
        value = None, 'a', {}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_attributes(self):
        data = '<a href="http://www.hforge.org">'
        token = START_ELEMENT
        value = None, 'a', {(None, 'href'): 'http://www.hforge.org'}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_attributes_single_quote(self):
        data = "<a href='http://www.hforge.org'>"
        token = START_ELEMENT
        value = None, 'a', {(None, 'href'): 'http://www.hforge.org'}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    def test_attributes_no_quote(self):
        data = "<a href=http://www.hforge.org>"
        self.assertRaises(XMLError, XMLParser(data).next)


    def test_attributes_forbidden_char(self):
        data = '<img title="Black & White">'
        self.assertRaises(XMLError, XMLParser(data).next)


    def test_attributes_entity_reference(self):
        data = '<img title="Black &amp; White">'
        token = START_ELEMENT
        value = None, 'img', {(None, 'title'): 'Black & White'}
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    #######################################################################
    # CDATA
    def test_cdata(self):
        data = '<![CDATA[Black & White]]>'
        token = CDATA
        value = 'Black & White'
        self.assertEqual(XMLParser(data).next(), (token, value, 1))


    #######################################################################
    # Broken XML
    def test_missing_end_element(self):
        data = '<div><span></div>'
        parser = XMLParser(data)
        self.assertRaises(XMLError, list, parser)


    def test_missing_end_element2(self):
        data = '<div>'
        parser = XMLParser(data)
        self.assertRaises(XMLError, list, parser)


class XMLTestCase(TestCase):

    #######################################################################
    # Identity
    def test_identity(self):
        """
        Tests wether the input and the output match.
        """
        data = ('<html>\n'
                '<head></head>\n'
                '<body>\n'
                ' this is a <span style="color: red">test</span>\n'
                '</body>\n'
                '</html>')
        h1 = XMLFile(string=data)
        h2 = XMLFile(string=data)

        self.assertEqual(h1, h2)


    #######################################################################
    # Entities: http://www.w3.org/TR/REC-xml/#sec-entexpand
    def test_1(self):
        data = ('<?xml version="1.0"?>\n'
                '<!DOCTYPE test\n'
                '[\n'
                '<!ENTITY example "<p>An ampersand (&#38;#38;) may be '
                'escaped numerically (&#38;#38;#38;) or with a general '
                ' entity (&amp;amp;).</p>" >\n'
                ']>\n'
                '<test>&example;</test>\n')

        parser = XMLParser(data)
        self.assertEqual(list(parser)[6:9], [
                  (2, (None, 'p', {}), 6),
                  (4, 'An ampersand (&) may be escaped numerically (&#38;) '
                      'or with a general  entity (&amp;).', 6),
                  (3, (None, 'p'), 6)])

    def test_2(self):
        data = ('<?xml version="1.0"?>\n'
                '<!DOCTYPE test [\n'
                '<!ELEMENT test (#PCDATA) >\n'
                "<!ENTITY % xx '&#37;zz;'>\n"
                """<!ENTITY % zz '&#60;!ENTITY tricky "error-prone" >' >\n"""
                '%xx;\n'
                ']>\n'
                '<test>This sample shows a &tricky; method.</test>')

        parser = XMLParser(data)
        self.assertEqual(list(parser)[5], (4,
                         'This sample shows a error-prone method.', 8))

    def test_3(self):
        data = ('<?xml version="1.0"?>\n'
                '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
                '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
                '<html>&laquo; &fnof; &Xi; &psi; &permil; &real; &infin; '
                '&there4; &clubs;</html>\n')
        expected = '« ƒ Ξ ψ ‰ ℜ ∞ ∴ ♣'

        parser = XMLParser(data)
        self.assertEqual(list(parser)[5][1], expected)


class DocTypeTestCase(TestCase):

    def test_1(self):
        dtd = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
               '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" '
               '[\n'
               '<!ENTITY entity_test "TEST">\n'
               ']>')
        data = '<?xml version="1.0"?>\n'+dtd

        parser = XMLParser(data)

        name, doctype = list(parser)[2][1]
        self.assertEqual(get_doctype(name, doctype), dtd)

    def test_2(self):
        dtd = ('PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
               '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" '
               '[\n'
               '<!ENTITY entity_test "TEST">\n'
               ']')
        doctype = DocType(PubidLiteral='-//W3C//DTD XHTML 1.0 Strict//EN',
                          SystemLiteral=
                          'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd',
                          intSubset='\n<!ENTITY entity_test "TEST">\n')
        self.assertEqual(doctype.to_str(), dtd)

    def test_3(self):
        doctype = DocType(PubidLiteral='-//W3C//DTD XHTML 1.0 Strict//EN',
                          SystemLiteral=
                          'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd',
                          intSubset='\n<!ENTITY entity_test "TEST">\n')
        data = '<html>&Agrave; &entity_test;</html>'

        # No raise
        list(XMLParser(data, doctype=doctype))


class TranslatableTestCase(TestCase):

    def test_surrounding(self):
        text = '<em>Hello World</em>'
        parser = XMLFile(string=text)

        messages = [unit[0] for unit in parser.get_units()]
        self.assertEqual(messages, [((srx_TEXT, u'Hello World'),)])



if __name__ == '__main__':
    unittest.main()
