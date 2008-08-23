# -*- coding: UTF-8 -*-
# Copyright (C) 2004, 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.gettext import POFile, Message
from itools.xml import XMLParser, XMLError, START_ELEMENT, END_ELEMENT, TEXT
from itools.xml import stream_to_str
from itools.html import HTMLFile, XHTMLFile, HTMLParser, sanitize_str
from itools.html.xhtml import stream_to_html



###########################################################################
# Test HTML
###########################################################################
def parse_tags(data):
    return [ (type, value[1]) for type, value, line in HTMLParser(data)
             if type == START_ELEMENT or type == END_ELEMENT ]


class HTMLParserTestCase(TestCase):

    def test_doctype(self):
        data = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
        stream = HTMLParser(data)
        self.assertEqual(stream_to_str(stream), data)


    def test_obvious(self):
        data = '<p></p>'
        expected = [(START_ELEMENT, 'p'), (END_ELEMENT, 'p')]
        self.assertEqual(parse_tags(data), expected)


    def test_empty(self):
        data = '<br>'
        expected = [(START_ELEMENT, 'br'), (END_ELEMENT, 'br')]
        self.assertEqual(parse_tags(data), expected)


    def test_ul(self):
        data = '<ul><li><li></li></ul>'
        expected = [
            (START_ELEMENT, 'ul'), (START_ELEMENT, 'li'), (END_ELEMENT, 'li'),
            (START_ELEMENT, 'li'), (END_ELEMENT, 'li'), (END_ELEMENT, 'ul')]
        self.assertEqual(parse_tags(data), expected)


    def test_forbidden(self):
        data = '<html><body><title></title></body></html>'
        expected = [
            (START_ELEMENT, 'html'), (START_ELEMENT, 'body'),
            (START_ELEMENT, 'title'), (END_ELEMENT, 'title'),
            (END_ELEMENT, 'body'), (END_ELEMENT, 'html')]
        self.assertEqual(parse_tags(data), expected)



    #######################################################################
    # Broken HTML
    #######################################################################
    def test_missing_end_element(self):
        data = '<div><span></div>'
        self.assertRaises(XMLError, HTMLParser, data)


    def test_missing_end_element2(self):
        data = '<div>'
        self.assertRaises(XMLError, HTMLParser, data)



class i18nTestCase(TestCase):

    def test_case1(self):
        """Test element content."""
        doc = HTMLFile(string=
            '<p>hello world</p>')

        messages = list(doc.get_units())
        self.assertEqual(messages, [Message([], [u'hello world'], [u''])])


    def test_case2(self):
        """Test simple attribute."""
        doc = HTMLFile(string=
            '<img alt="The beach" src="beach.jpg">')

        messages = list(doc.get_units())
        self.assertEqual(messages, [Message([], [u'The beach'], [u''])])


    def test_case3(self):
        """Test complex attribute."""
        doc = HTMLFile(string=
            '<html>\n'
            '<input type="text" name="id">\n'
            '<input type="submit" value="Change">\n'
            '</html>')

        messages = list(doc.get_units())
        self.assertEqual(messages, [Message([], [u'Change'], [u''])])


    def test_case4(self):
        """Test translation of an element content"""
        doc = HTMLFile(string=
            '<p>hello world</p>')

        p = POFile(string=
            'msgid "hello world"\n'
            'msgstr "hola mundo"')

        self.assertEqual(doc.translate(p), '<p>hola mundo</p>')


    def test_case5(self):
        """Test translation of an element content"""
        doc = HTMLFile(string=
            '<img alt="The beach" src="beach.jpg">')

        po = POFile(string=
            'msgid "The beach"\n'
             'msgstr "La playa"')

        string = doc.translate(po)
        output = HTMLFile(string=string)

        expected = HTMLFile(string=
            '<img alt="La playa" src="beach.jpg">')
        self.assertEqual(output, expected)


    def test_case6(self):
        """Test translation of an element content"""
        doc = HTMLFile(string=
            '<input type="text" name="id">\n'
            '<input type="submit" value="Change">')

        p = POFile(string=
            'msgid "Change"\n'
            'msgstr "Cambiar"')

        output = HTMLFile(string=doc.translate(p))

        expected = HTMLFile(string=
            '<input type="text" name="id">\n'
            '<input type="submit" value="Cambiar">')
        self.assertEqual(output, expected)


    def test_translation1(self):
        """Test translation with surrounding tags"""

        doc = HTMLFile(string =
            '<em>hello world</em>')

        p = POFile(string=
            'msgid "hello world"\n'
            'msgstr "hola mundo"')

        self.assertEqual(doc.translate(p), '<em>hola mundo</em>')


    def test_translation2(self):
        """Test translation with surrounding tags (2)"""

        doc = HTMLFile(string =
            'Say: <em>hello world. It\'s me.</em>')

        p = POFile(string=
            'msgid "Say:"\n'
            'msgstr "Dice:"\n\n'
            'msgid "hello world."\n'
            'msgstr "hola mundo."\n\n'
            'msgid "It\'s me."\n'
            'msgstr "Es me."')

        self.assertEqual(doc.translate(p), 'Dice: <em>hola mundo. Es me.</em>')


    def test_translation3(self):
        """Test translation with surrounding tags (3)"""

        doc = HTMLFile(string =
            'Say: <em> hello world. It\'s me.</em> Do you remember me ?')

        p = POFile(string=
            'msgid "Say:"\n'
            'msgstr "Dites:"\n\n'
            'msgid "hello world."\n'
            'msgstr "Bonjour monde."\n\n'
            'msgid "It\'s me."\n'
            'msgstr "C\'est moi."\n\n'
            'msgid "Do you remember me ?"\n'
            'msgstr "Vous vous rappelez de moi ?"')

        self.assertEqual(doc.translate(p),
                         'Dites: <em> Bonjour monde. C\'est moi.</em> '
                         'Vous vous rappelez de moi ?')


    def test_translation4(self):
        """Test translation with surrounding tags (4)"""

        doc = HTMLFile(string =
            'Say: <em>   hello world. It\'s me.</em>'
            '      Do you remember me ?  ')

        p = POFile(string=
            'msgid "Say:"\n'
            'msgstr "Dites:"\n\n'
            'msgid "hello world."\n'
            'msgstr "Bonjour monde."\n\n'
            'msgid "It\'s me."\n'
            'msgstr "C\'est moi."\n\n'
            'msgid "Do you remember me ?"\n'
            'msgstr "Vous vous rappelez de moi ?"')

        self.assertEqual(doc.translate(p), 'Dites: '
                         '<em>   Bonjour monde. C\'est moi.</em>'
                         '      Vous vous rappelez de moi ? ')


    def test_pre(self):
        """Test raw content."""
        doc = HTMLFile(string = '<pre>   This is raw text, and every '
                                'characters should be kept </pre>')

        messages = list(doc.get_units())
        expected = u'   This is raw text, and every characters should be kept '
        self.assertEqual(messages, [Message([], [expected], [u''])])


###########################################################################
# Test XHTML
###########################################################################
class SerializationTestCase(TestCase):

    def test_stream_to_html_escape(self):
        parser = XMLParser('<p xmlns="http://www.w3.org/1999/xhtml"></p>')
        events = list(parser)
        events.insert(1, (TEXT, '<br/>', 0))

        self.assertEqual(
            stream_to_html(events),
            '<p xmlns="http://www.w3.org/1999/xhtml">&lt;br/></p>')


    def test_html(self):
        parser = XMLParser(
            '<p xmlns="http://www.w3.org/1999/xhtml">Bed&amp;Breakfast</p>')
        out = stream_to_html(parser)
        # Assert
        self.assertEqual(out,
            '<p xmlns="http://www.w3.org/1999/xhtml">Bed&amp;Breakfast</p>')



class SegmentationTestCase(TestCase):

    def test_paragraph(self):
        """Test formatted paragraph"""
        doc = XHTMLFile(string=
            '<p xmlns="http://www.w3.org/1999/xhtml">\n'
            'The Mozilla project maintains <em>choice</em> and\n'
            '<em>innovation</em> on the Internet. Developing the\n'
            'acclaimed, <em>open source</em>, <b>Mozilla 1.6</b>.\n'
            '</p>')

        messages = list(doc.get_units())
        msg1 = (u'The Mozilla project maintains <em>choice</em> and'
                u' <em>innovation</em> on the Internet.')
        msg2 = (u'Developing the acclaimed, <em>open source</em>,'
                u' <b>Mozilla 1.6</b>.')
        expected = [Message([], [msg1], [u'']), Message([], [msg2], [u''])]
        self.assertEqual(messages, expected)


    def test_table(self):
        doc = XHTMLFile(string=
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

        messages = list(doc.get_units())
        expected = [Message([], [u'Title'], [u'']),
                    Message([], [u'Size'], [u'']),
                    Message([], [u'The good, the bad and the ugly'], [u'']),
                    Message([], [u'looong'], [u'']),
                    Message([], [u'Love story'], [u'']),
                    Message([], [u'even longer'], [u''])]
        self.assertEqual(messages, expected)


    def test_random(self):
        """Test element content."""
        # The document
        doc = XHTMLFile(string=
            '<body xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <p>this <em>word</em> is nice</p>\n'
            '  <a href="/"><img src="logo.png" /></a>\n'
            '  <p><em>hello world</em></p><br/>'
            '  bye <em>J. David Ibanez Palomar</em>\n'
            '</body>')

        messages = list(doc.get_units())
        expected = [Message([], [u'this <em>word</em> is nice'], [u'']),
                    Message([], [u'hello world'], [u'']),
                    Message([], [u'<br/> bye <em>J. David Ibanez '
                                 u'Palomar</em>'], [u''])]
        self.assertEqual(messages, expected)


    def test_form(self):
        """Test complex attribute."""
        # The document
        doc = XHTMLFile(string=
            '<form xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <input type="text" name="id" />\n'
            '  <input type="submit" value="Change" />\n'
            '</form>')

        messages = list(doc.get_units())
        self.assertEqual(messages, [Message([], [u'Change'], [u''])])


    def test_inline(self):
        doc = XHTMLFile(string=
            '<p xmlns="http://www.w3.org/1999/xhtml">'
            'Hi <b>everybody, </b><i>how are you ? </i>'
            '</p>')

        messages = doc.get_units()
        messages = list(messages)

        expected = [Message([], [u'Hi <b>everybody, </b><i>how are you ? '
                                 u'</i>'], [u''])]
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
        doc = XHTMLFile(string=data)
        messages = list(doc.get_units())

        self.assertEqual(messages, [Message([], [u'hello litle world'],
                                            [u''])])


    def test_case2(self):
        """Test simple attribute."""
        data = self.template % '<img alt="The beach" src="beach.jpg" />'
        doc = XHTMLFile(string=data)
        messages = list(doc.get_units())

        self.assertEqual(messages, [Message([], [u'The beach'], [u''])])


    def test_case3(self):
        """Test complex attribute."""
        data = self.template % ('<input type="text" name="id" />\n'
                                '<input type="submit" value="Change" />')
        doc = XHTMLFile(string=data)
        messages = list(doc.get_units())

        self.assertEqual(messages, [Message([], [u'Change'], [u''])])


    def test_case4(self):
        """Test translation of an element content"""
        string = (
            'msgid "hello world"\n'
            'msgstr "hola mundo"\n')
        p = POFile(string=string)

        string = self.template % '<p>hello world</p>'
        source = XHTMLFile(string=string)

        string = source.translate(p)
        xhtml = XHTMLFile(string=string)

        messages = list(xhtml.get_units())
        self.assertEqual(messages, [Message([], [u'hola mundo'], [u''])])


    def test_case5(self):
        """Test translation of an element content"""
        po = POFile(string=
            'msgid "The beach"\n'
            'msgstr "La playa"')
        xhtml = XHTMLFile(string=
            self.template  % '<img alt="The beach" src="beach.jpg" />')

        html = xhtml.translate(po)
        xhtml = XHTMLFile(string=html)

        messages = list(xhtml.get_units())
        self.assertEqual(messages, [Message([], [u'La playa'], [u''])])


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
