# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2004, 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
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
from itools.xml import Parser, TEXT
from itools.xhtml import Document
from itools.xhtml.xhtml import stream_to_html, sanitize_str
from itools.gettext import PO



class SerializationTestCase(TestCase):

    def test_stream_to_html_escape(self):
        parser = Parser('<p xmlns="http://www.w3.org/1999/xhtml"></p>')
        events = list(parser)
        events.insert(1, (TEXT, '<br/>', 0))

        self.assertEqual(
            stream_to_html(events),
            '<p xmlns="http://www.w3.org/1999/xhtml">&lt;br/></p>')


    def test_html(self):
        parser = Parser(
            '<p xmlns="http://www.w3.org/1999/xhtml">Bed&amp;Breakfast</p>')
        out = stream_to_html(parser)
        # Assert
        self.assertEqual(out,
            '<p xmlns="http://www.w3.org/1999/xhtml">Bed&amp;Breakfast</p>')



class SegmentationTestCase(TestCase):

    def test_paragraph(self):
        """Test formatted paragraph"""
        doc = Document(string=
            '<p xmlns="http://www.w3.org/1999/xhtml">\n'
            'The Mozilla project maintains <em>choice</em> and\n'
            '<em>innovation</em> on the Internet. Developing the\n'
            'acclaimed, <em>open source</em>, <b>Mozilla 1.6</b>.\n'
            '</p>')

        messages = list(doc.get_messages())
        expected = [(u'The Mozilla project maintains <em>choice</em> and'
                     u' <em>innovation</em> on the Internet.', 0),
                    (u'Developing the acclaimed, <em>open source</em>,'
                     u' <b>Mozilla 1.6</b>.', 0)]
        self.assertEqual(messages, expected)


    def test_table(self):
        doc = Document(string=
            '<table xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <tr>\n'
            '    <th>Title</th>\n'
            '    <th>Size</th>\n'
            '  </tr>\n'
            '  <tr>\n'
            '    <td>The good, the bad and the ugly</td>\n'
            '    <td>looong</td>\n'
            '  </tr>\n'
            '  <tr>\n'
            '    <td>Love story</td>\n'
            '    <td>even longer</td>\n'
            '  </tr>\n'
            '</table>')

        messages = list(doc.get_messages())
        expected = [(u'Title', 0),
                    (u'Size', 0),
                    (u'The good, the bad and the ugly', 0),
                    (u'looong', 0),
                    (u'Love story', 0),
                    (u'even longer', 0)]
        self.assertEqual(messages, expected)


    def test_random(self):
        """Test element content."""
        # The document
        doc = Document(string=
            '<body xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <p>this <em>word</em> is nice</p>\n'
            '  <a href="/"><img src="logo.png" /></a>\n'
            '  <p><em>hello world</em></p><br/>'
            '  bye <em>J. David Ibanez Palomar</em>\n'
            '</body>')

        messages = list(doc.get_messages())
        expected = [(u'this <em>word</em> is nice', 0),
                    (u'hello world', 0),
                    (u'<br/> bye <em>J. David Ibanez Palomar</em>', 0)]
        self.assertEqual(messages, expected)


    def test_form(self):
        """Test complex attribute."""
        # The document
        doc = Document(string=
            '<form xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <input type="text" name="id" />\n'
            '  <input type="submit" value="Change" />\n'
            '</form>')

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'Change', 0)])


    def test_inline(self):
        doc = Document(string=
            '<p xmlns="http://www.w3.org/1999/xhtml">'
            'Hi <b>everybody, </b><i>how are you ? </i>'
            '</p>')

        messages = doc.get_messages()
        messages = list(messages)

        expected = [(u'Hi <b>everybody, </b><i>how are you ? </i>', 0)]
        self.assertEqual(messages, expected)



class TranslationTestCase(TestCase):

    def setUp(self):
        self.template = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n'
            '  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <head></head>\n'
            '  <body>%s</body>\n'
            '</html>\n')
 

    def test_case1(self):
        """Test element content."""
        data = self.template % '<p>hello litle world</p>'
        doc = Document(string=data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'hello litle world', 0)])


    def test_case2(self):
        """Test simple attribute."""
        data = self.template % '<img alt="The beach" src="beach.jpg" />' 
        doc = Document(string=data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'The beach', 0)])


    def test_case3(self):
        """Test complex attribute."""
        data = self.template % ('<input type="text" name="id" />\n'
                                '<input type="submit" value="Change" />')
        doc = Document(string=data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'Change', 0)])


    def test_case4(self):
        """Test translation of an element content"""
        string = (
            'msgid "hello world"\n'
            'msgstr "hola mundo"\n')
        p = PO(string=string)

        string = self.template % '<p>hello world</p>'
        source = Document(string=string)

        string = source.translate(p)
        xhtml = Document(string=string)

        messages = list(xhtml.get_messages())
        self.assertEqual(messages, [(u'hola mundo', 0)])


    def test_case5(self):
        """Test translation of an element content"""
        po = PO(string=
            'msgid "The beach"\n'
            'msgstr "La playa"')
        xhtml = Document(string=
            self.template  % '<img alt="The beach" src="beach.jpg" />')

        html = xhtml.translate(po)
        xhtml = Document(string=html)

        messages = list(xhtml.get_messages())
        self.assertEqual(messages, [(u'La playa', 0)])


class SanitizerTestCase(TestCase):

    def test_javascript(self):
        data = '<div><script>alert("Hello world")</script></div>'
        stream = sanitize_str(data)
        data_return = stream_to_html(stream)
        expected = '<div></div>'
        self.assertEqual(data_return, expected)


    def test_css(self):
        data = '<div style="background: url(javascript:void);"></div>'
        stream = sanitize_str(data)
        data_return = stream_to_html(stream)
        expected = '<div></div>'
        self.assertEqual(data_return, expected)


    def test_onmouseover(self):
        data = '<b onMouseOver="self.location.href=\'www.free.fr\'">Hello</b>'
        stream = sanitize_str(data)
        data_return = stream_to_html(stream)
        expected = '<b>Hello</b>'
        self.assertEqual(data_return, expected)


    def test_links(self):
        data = '<a href="javascript:alert(\'Hello\')">Hello World</a>'
        stream = sanitize_str(data)
        data_return = stream_to_html(stream)
        expected = '<a>Hello World</a>'
        self.assertEqual(data_return, expected)


    def test_comment(self):
        data = '<!-- javascript:alert("Hello"); -->'
        stream = sanitize_str(data)
        data_return = stream_to_html(stream)
        expected = ''
        self.assertEqual(data_return, expected)


if __name__ == '__main__':
    unittest.main()
