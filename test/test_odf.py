# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.odf import ODTFile, ODPFile, ODSFile
from itools.gettext import POFile, Message
from itools import vfs
from itools.xml import XMLParser
from itools.xml.i18n import get_messages, translate


class Test_ODT_File(TestCase):

    def setUp(self):
        file = vfs.open('odf/Document.odt')
        self.doc = ODTFile()
        self.doc.load_state_from_file(file)


    def test_get_msg(self):
        messages = list(self.doc.get_messages())
        expected_messages = [
            # content.xml
            u'Hello <text:span text:style-name="T1">world</text:span> !',
            # meta.xml
            u'Hello world Document', u'it\'s a very good document',
            u'Itools test', u'sylvain', u'sylvain', u'itools', u'odt', u'odf']
        expected = []
        for msg in expected_messages:
            expected.append(Message([], [msg], [u'']))
        self.assertEqual(messages, expected)


    def test_translation(self):
        # Translate the document
        str = ('msgid "Hello <text:span text:style-name="T1">world</text:span> !"\n'
        'msgstr "Hola <text:span text:style-name="T1">mundo</text:span> !"\n')
        po = POFile(string=str)
        translate_odt_document = self.doc.translate(po)
        # Get the message of the translate document
        doc2 = ODTFile()
        doc2.load_state_from_string(translate_odt_document)
        messages = list(doc2.get_messages())
        # Check if allright
        expected_messages = [
            # content.xml
            u'Hola <text:span text:style-name="T1">mundo</text:span> !',
            # meta.xml
            u'Hello world Document', u'it\'s a very good document',
            u'Itools test', u'sylvain', u'sylvain', u'itools', u'odt', u'odf']
        expected =  []
        for msg in expected_messages:
            expected.append(Message([], [msg], [u'']))
        self.assertEqual(messages, expected)


    def test_meta(self):
        expected_meta = {'initial-creator': u'sylvain',
                         'description': u"it's a very good document",
                         'keyword': u'itools\nodt\nodf',
                         'creator': u'sylvain',
                         'title': u'Hello world Document',
                         'language': u'fr-FR',
                         'creation-date': u'2007-06-01T11:25:20',
                         'date': u'2007-06-03T21:26:04',
                         'subject': u'Itools test'}

        meta = self.doc.get_meta()
        self.assertEqual(expected_meta, meta)



class Test_ODP_File(TestCase):

    def setUp(self):
        file = vfs.open('odf/Document.odp')
        self.doc = ODPFile()
        self.doc.load_state_from_file(file)


    def test_get_msg(self):
        messages = list(self.doc.get_messages())
        expected_messages = [
            # content.xml
            u'<text:span text:style-name="T1">Hello </text:span>'
            '<text:span text:style-name="T2">World</text:span>'
            '<text:span text:style-name="T1"> !</text:span>',
            u'Welcome',
            # meta.xml
            u'sylvain', u'sylvain',
            # styles
            u'2', u'2', u'2']
        expected = []
        for msg in expected_messages:
            expected.append(Message([],[msg], [u'']))
        self.assertEqual(messages, expected)




class Test_ODS_File(TestCase):

    def setUp(self):
        file = vfs.open('odf/Document.ods')
        self.doc = ODSFile()
        self.doc.load_state_from_file(file)

    def test_get_msg(self):
        messages = list(self.doc.get_messages())
        expected_messages = [# content.xml
                             u'Chocolate', u'Coffee', u'Tea', u'Price', u'80',
                             u'20', u'40', u'Quantity', u'20', u'30', u'20',
                             u'Quality', u'0', u'50', u'40',
                             # meta.xml
                             u'sylvain', u'sylvain',
                             # styles.xml
                             u'-', u'-', u'???',
                             u'Page <text:page-number>1</text:page-number>',
                             u'???', u'(', u'???', u')', u',',
                             u'Page <text:page-number>1</text:page-number> / '
                             u'<text:page-count>99</text:page-count>']
        expected = []
        for msg in expected_messages:
            expected.append(Message([],[msg], [u'']))
        self.assertEqual(messages, expected)



class Test_ODT_Parser(TestCase):

    def setUp(self):
        self.template = (
       '<?xml version="1.0" encoding="UTF-8"?>'
       '<office:document-content '
       'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
       'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
       'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
       'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
       'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
       'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
       'xmlns:xlink="http://www.w3.org/1999/xlink" '
       'xmlns:dc="http://purl.org/dc/elements/1.1/" '
       'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
       'xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0" '
       'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" '
       'xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" '
       'xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" '
       'xmlns:math="http://www.w3.org/1998/Math/MathML" '
       'xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" '
       'xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" '
       'xmlns:ooo="http://openoffice.org/2004/office" '
       'xmlns:ooow="http://openoffice.org/2004/writer" '
       'xmlns:oooc="http://openoffice.org/2004/calc" '
       'xmlns:dom="http://www.w3.org/2001/xml-events" '
       'xmlns:xforms="http://www.w3.org/2002/xforms" '
       'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
       'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
       ' office:version="1.0">'
       '<office:body>'
       '%s'
       '</office:body>'
       '</office:document-content>')


    def test_paragraph(self):
        """Test formatted paragraph"""
        content = ('<office:text>'
                   '<text:p text:style-name="Standard">'
                   'hello world'
                   '</text:p>'
                   '</office:text>')
        content = self.template % content
        events = XMLParser(content)
        messages = list(get_messages(events))
        expected = [Message([], [u'hello world'], [u''])]
        self.assertEqual(messages, expected)

    def test_table(self):
        content = """
        <office:text>
        <table:table table:name="Tableau1" table:style-name="Tableau1">
        <table:table-column table:style-name="Tableau1.A"
        table:number-columns-repeated="3"/>
        <table:table-row>
        <table:table-cell table:style-name="Tableau1.A1" office:value-type="string">
        <text:p text:style-name="Table_20_Contents">A</text:p>
        </table:table-cell>
        <table:table-cell table:style-name="Tableau1.A1" office:value-type="string">
        <text:p text:style-name="Table_20_Contents">B</text:p>
        </table:table-cell>
        <table:table-cell table:style-name="Tableau1.C1" office:value-type="string">
        <text:p text:style-name="Table_20_Contents">C</text:p>
        </table:table-cell>
        </table:table-row>
        <table:table-row>
        <table:table-cell table:style-name="Tableau1.A2" office:value-type="string">
        <text:p text:style-name="Table_20_Contents">D</text:p>
        </table:table-cell>
        <table:table-cell table:style-name="Tableau1.A2" office:value-type="string">
        <text:p text:style-name="Table_20_Contents">E</text:p>
        </table:table-cell>
        <table:table-cell table:style-name="Tableau1.C2" office:value-type="string">
        <text:p text:style-name="Table_20_Contents">F</text:p>
        </table:table-cell>
        </table:table-row>
        </table:table>
        </office:text>
                  """

        content = self.template % content
        events = XMLParser(content)
        messages = list(get_messages(events))
        expected= [Message([], [u'A'], [u'']), Message([], [u'B'], [u'']),
                   Message([], [u'C'], [u'']), Message([], [u'D'], [u'']),
                   Message([], [u'E'], [u'']), Message([], [u'F'], [u''])]
        self.assertEqual(messages, expected)


    def test_translation_paragraph(self):
        """Test translation of an element content"""
        po = POFile(string=
            'msgid "hello world"\n'
            'msgstr "hola mundo"\n')
        content = ('<office:text>'
                   '<text:p text:style-name="Standard">'
                   'hello world'
                   '</text:p>'
                   '</office:text>')

        content = self.template % content
        events = XMLParser(content)
        string = translate(events, po)
        messages = list(get_messages(string))
        self.assertEqual(messages, [Message([], [u'hola mundo'], [u''])])


if __name__ == '__main__':
    unittest.main()
