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
from unittest import TestCase, main

# Import from itools
import itools.html
from itools.xml import XMLParser, DocType, XMLError, XML_DECL, START_ELEMENT
from itools.xml import TEXT, CDATA, get_doctype


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



if __name__ == '__main__':
    main()
