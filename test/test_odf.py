# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
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
from itools.gettext import POFile, POUnit
from itools.odf import ODTFile, ODPFile, ODSFile
from itools.srx import TEXT, START_FORMAT, END_FORMAT
from itools.xml import XMLParser
from itools.xmlfile import get_units, translate


class Test_ODT_File(TestCase):

    def setUp(self):
        self.doc = ODTFile('odf/Document.odt')


    def test_get_msg(self):
        messages = [unit[0] for unit in self.doc.get_units()]
        expected = [((TEXT, u'Hello '), (START_FORMAT, 1), (TEXT, u'world'),
                     (END_FORMAT, 1), (TEXT, u' !')),
                    ((TEXT, u'Hello world Document'),),
                    ((TEXT, u"it's a very good document"),),
                    ((TEXT, u'Itools test'),),
                    ((TEXT, u'itools'),),
                    ((TEXT, u'odt'),),
                    ((TEXT, u'odf'),)]

        self.assertEqual(messages, expected)


    def test_translation(self):
        # Translate the document
        str = ('msgid "Hello <text:span text:style-name="T1">world</text:span>'
               ' !"\nmsgstr "Hola '
               '<text:span text:style-name="T1">mundo</text:span> !"\n')
        po = POFile(string=str)
        # Get the message of the translate document
        translated_doc = self.doc.translate(po)
        translated_doc = ODTFile(string=translated_doc)
        messages = [unit[0] for unit in translated_doc.get_units()]
        # Check if allright
        expected = [
            # content.xml
            ((TEXT, u'Hello '), (START_FORMAT, 1), (TEXT, u'world'),
             (END_FORMAT, 1), (TEXT, u' !')),
            # meta.xml
            ((TEXT, u'Hello world Document'),),
            ((TEXT, u"it's a very good document"),),
            ((TEXT, u'Itools test'),),
            ((TEXT, u'itools'),),
            ((TEXT, u'odt'),),
            ((TEXT, u'odf'),)]

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
        self.doc = ODPFile('odf/Document.odp')


    def test_get_msg(self):
        messages = [unit[0] for unit in self.doc.get_units()]
        expected = [((START_FORMAT, 1), (TEXT, u'Hello '), (END_FORMAT, 1),
                     (START_FORMAT, 2), (TEXT, u'World'), (END_FORMAT, 2),
                     (START_FORMAT, 3), (TEXT, u' !'), (END_FORMAT, 3)),
                    ((TEXT, u'Welcome'),),
                    ((TEXT, u'2'),),
                    ((TEXT, u'2'),),
                    ((TEXT, u'2'),)]

        self.assertEqual(messages, expected)



class Test_ODS_File(TestCase):

    def setUp(self):
        self.doc = ODSFile('odf/Document.ods')

    def test_get_msg(self):
        messages = [unit[0] for unit in self.doc.get_units()]
        expected = [((TEXT, u'Chocolate'),),
                    ((TEXT, u'Coffee'),),
                    ((TEXT, u'Tea'),),
                    ((TEXT, u'Price'),),
                    ((TEXT, u'80'),),
                    ((TEXT, u'20'),),
                    ((TEXT, u'40'),),
                    ((TEXT, u'Quantity'),),
                    ((TEXT, u'20'),),
                    ((TEXT, u'30'),),
                    ((TEXT, u'20'),),
                    ((TEXT, u'Quality'),),
                    ((TEXT, u'0'),),
                    ((TEXT, u'50'),),
                    ((TEXT, u'40'),),
                    ((TEXT, u'-'),),
                    ((TEXT, u'-'),),
                    ((TEXT, u'Page '), (START_FORMAT, 1), (TEXT, u'1'),
                     (END_FORMAT, 1)),
                    ((TEXT, u'('),),
                    ((TEXT, u'???'),),
                    ((TEXT, u')'),),
                    ((TEXT, u','),),
                    ((TEXT, u'Page '), (START_FORMAT, 2), (TEXT, u'1'),
                     (END_FORMAT, 2), (TEXT, u' /'))]

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
        messages = XMLParser(content)
        messages = [unit[0] for unit in get_units(messages)]
        expected = [((TEXT, u'hello world'),)]
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
        messages = XMLParser(content)
        messages = [unit[0] for unit in get_units(messages)]
        expected= [((TEXT, u'A'),),
                   ((TEXT, u'B'),),
                   ((TEXT, u'C'),),
                   ((TEXT, u'D'),),
                   ((TEXT, u'E'),),
                   ((TEXT, u'F'),)]

        self.assertEqual(messages, expected)


    def test_translation_paragraph(self):
        """Test translation of an element content"""
        po = POFile(string=
            'msgctxt "paragraph"\n'
            'msgid "hello world"\n'
            'msgstr "hola mundo"\n')
        content = ('<office:text>'
                   '<text:p text:style-name="Standard">'
                   'hello world'
                   '</text:p>'
                   '</office:text>')

        content = self.template % content
        messages = XMLParser(content)
        messages = translate(messages, po)
        messages = [unit[0] for unit in get_units(messages)]
        self.assertEqual(messages, [((TEXT, u'hola mundo'),)])


if __name__ == '__main__':
    main()
