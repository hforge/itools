# -*- coding: UTF-8 -*-
# Copyright (C) 2004, 2006-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
# Copyright (C) 2008 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from itools.gettext import POFile
from itools.html import HTMLFile, XHTMLFile, HTMLParser, sanitize_str
from itools.html.xhtml import stream_to_html
from itools.srx import TEXT, START_FORMAT, END_FORMAT
from itools.xml import XMLParser, XMLError, START_ELEMENT, END_ELEMENT
from itools.xml import TEXT as xml_TEXT, stream_to_str



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
        doc = HTMLFile(string='<p>hello world</p>')

        messages = [unit[0] for unit in doc.get_units()]
        self.assertEqual(messages, [((TEXT, u'hello world'),)])


    def test_case2(self):
        """Test simple attribute."""
        doc = HTMLFile(string='<img alt="The beach" src="beach.jpg">')

        messages = [unit[0] for unit in doc.get_units()]
        self.assertEqual(messages, [((TEXT, u'The beach'),)])


    def test_case3(self):
        """Test complex attribute."""
        doc = HTMLFile(string=
            '<html>\n'
            '<input type="text" name="id">\n'
            '<input type="submit" value="Change">\n'
            '</html>')

        messages = [unit[0] for unit in doc.get_units()]
        self.assertEqual(messages, [((TEXT, u'Change'),)])


    def test_case4(self):
        """Test translation of an element content"""
        doc = HTMLFile(string='<p>hello world</p>')

        p = POFile(string=
            'msgctxt "paragraph"\n'
            'msgid "hello world"\n'
            'msgstr "hola mundo"')

        self.assertEqual(doc.translate(p), '<p>hola mundo</p>')


    def test_case5(self):
        """Test translation of an element content"""
        doc = HTMLFile(string='<img alt="The beach" src="beach.jpg">')

        po = POFile(string=
            'msgctxt "img[alt]"\n'
            'msgid "The beach"\n'
            'msgstr "La playa"')

        string = doc.translate(po)
        output = HTMLFile(string=string)

        expected = HTMLFile(string='<img alt="La playa" src="beach.jpg">')
        self.assertEqual(output, expected)


    def test_case6(self):
        """Test translation of an element content"""
        doc = HTMLFile(string=
            '<input type="text" name="id">'
            '<input type="submit" value="Change">')

        p = POFile(string=
            'msgctxt "button"\n'
            'msgid "Change"\n'
            'msgstr "Cambiar"')

        output = HTMLFile(string=doc.translate(p))

        expected = HTMLFile(string=
            '<input type="text" name="id">'
            '<input type="submit" value="Cambiar">')
        self.assertEqual(output.to_str(), expected.to_str())


    def test_translation1(self):
        """Test translation with surrounding tags"""

        doc = HTMLFile(string='<em>hello world</em>')

        p = POFile(string=
            'msgctxt "emphasis"\n'
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
            'msgctxt "emphasis"\n'
            'msgid "hello world."\n'
            'msgstr "hola mundo."\n\n'
            'msgctxt "emphasis"\n'
            'msgid "It\'s me."\n'
            'msgstr "Es me."')

        self.assertEqual(doc.translate(p),
                         'Dice: <em>hola mundo. Es me.</em>')


    def test_translation3(self):
        """Test translation with surrounding tags (3)"""

        doc = HTMLFile(string =
            'Say: <em> hello world. It\'s me.</em> Do you remember me ?')

        p = POFile(string=
            'msgid "Say:"\n'
            'msgstr "Dites:"\n\n'
            'msgctxt "emphasis"\n'
            'msgid "hello world."\n'
            'msgstr "Bonjour monde."\n\n'
            'msgctxt "emphasis"\n'
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
            '      Do you remember me ? ')

        p = POFile(string=
            'msgid "Say:"\n'
            'msgstr "Dites:"\n\n'
            'msgctxt "emphasis"\n'
            'msgid "hello world."\n'
            'msgstr "Bonjour monde."\n\n'
            'msgctxt "emphasis"\n'
            'msgid "It\'s me."\n'
            'msgstr "C\'est moi."\n\n'
            'msgid "Do you remember me ?"\n'
            'msgstr "Vous vous rappelez de moi ?"')

        self.assertEqual(doc.translate(p), 'Dites: '
                         '<em>   Bonjour monde. C\'est moi.</em>'
                         '      Vous vous rappelez de moi ? ')


    def test_pre(self):
        """Test raw content."""
        doc = HTMLFile(string = '<pre>   This is raw text, "     \n"'
                                ' </pre>')

        messages = [unit[0] for unit in doc.get_units()]
        expected = [((TEXT, u'This is raw text, "     \n"'),)]
        self.assertEqual(messages, expected)


###########################################################################
# Test XHTML
###########################################################################
class SerializationTestCase(TestCase):

    def test_stream_to_html_escape(self):
        parser = XMLParser('<p xmlns="http://www.w3.org/1999/xhtml"></p>')
        events = list(parser)
        events.insert(1, (xml_TEXT, '<br/>', 0))

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

        messages = [unit[0] for unit in doc.get_units()]
        expected = [((TEXT, u'The Mozilla project maintains '),
                     (START_FORMAT, 1), (TEXT, u'choice'), (END_FORMAT, 1),
                     (TEXT, u' and '), (START_FORMAT, 2),
                     (TEXT, u'innovation'), (END_FORMAT, 2),
                     (TEXT, u' on the Internet.')),
                    ((TEXT, u'Developing the acclaimed, '),
                     (START_FORMAT, 3), (TEXT, u'open source'),
                     (END_FORMAT, 3), (TEXT, u', '), (START_FORMAT, 4),
                     (TEXT, u'Mozilla 1.6'), (END_FORMAT, 4), (TEXT, u'.'))]
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

        messages = [unit[0] for unit in doc.get_units()]
        expected = [((TEXT, u'Title'),), ((TEXT, u'Size'),),
                    ((TEXT, u'The good, the bad and the ugly'),),
                    ((TEXT, u'looong'),), ((TEXT, u'Love story'),),
                    ((TEXT, u'even longer'),)]

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

        messages = [unit[0] for unit in doc.get_units()]
        expected = [((TEXT, u'this '), (START_FORMAT, 1), (TEXT, u'word'),
                     (END_FORMAT, 1), (TEXT, u' is nice')),
                    ((TEXT, u'hello world'),), ((TEXT, u'bye '),
                     (START_FORMAT, 6), (TEXT, u'J. David Ibanez Palomar'),
                     (END_FORMAT, 6))]

        self.assertEqual(messages, expected)


    def test_form(self):
        """Test complex attribute."""
        # The document
        doc = XHTMLFile(string=
            '<form xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <input type="text" name="id" />\n'
            '  <input type="submit" value="Change" />\n'
            '</form>')

        messages = [unit[0] for unit in doc.get_units()]
        self.assertEqual(messages, [((TEXT, u'Change'),)])


    def test_inline(self):
        doc = XHTMLFile(string=
            '<p xmlns="http://www.w3.org/1999/xhtml">'
            'Hi <b>everybody, </b><i>how are you ? </i>'
            '</p>')

        messages = [unit[0] for unit in doc.get_units()]
        expected = [((TEXT, u'Hi '), (START_FORMAT, 1),
                     (TEXT, u'everybody, '), (END_FORMAT, 1),
                     (START_FORMAT, 2), (TEXT, u'how are you ? '),
                     (END_FORMAT, 2))]
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
        data = self.template % '<p>hello little world</p>'
        doc = XHTMLFile(string=data)

        messages = [unit[0] for unit in doc.get_units()]
        self.assertEqual(messages, [((TEXT, u'hello little world'),)])


    def test_case2(self):
        """Test simple attribute."""
        data = self.template % '<img alt="The beach" src="beach.jpg" />'
        doc = XHTMLFile(string=data)

        messages = [unit[0] for unit in doc.get_units()]
        self.assertEqual(messages, [((TEXT, u'The beach'),)])


    def test_case3(self):
        """Test complex attribute."""
        data = self.template % ('<input type="text" name="id" />\n'
                                '<input type="submit" value="Change" />')
        doc = XHTMLFile(string=data)

        messages = [unit[0] for unit in doc.get_units()]
        self.assertEqual(messages, [((TEXT, u'Change'),)])


    def test_case4(self):
        """Test translation of an element content"""
        string = (
            'msgctxt "paragraph"\n'
            'msgid "hello world"\n'
            'msgstr "hola mundo"\n')
        p = POFile(string=string)

        string = self.template % '<p>hello world</p>'
        source = XHTMLFile(string=string)

        string = source.translate(p)
        xhtml = XHTMLFile(string=string)

        messages = [unit[0] for unit in xhtml.get_units()]
        self.assertEqual(messages, [((TEXT, u'hola mundo'),)])


    def test_case5(self):
        """Test translation of an element content"""
        po = POFile(string=
            'msgctxt "img[alt]"\n'
            'msgid "The beach"\n'
            'msgstr "La playa"')
        xhtml = XHTMLFile(string=
            self.template  % '<img alt="The beach" src="beach.jpg" />')

        html = xhtml.translate(po)
        xhtml = XHTMLFile(string=html)

        messages = [unit[0] for unit in xhtml.get_units()]
        self.assertEqual(messages, [((TEXT, u'La playa'),)])


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
    main()
