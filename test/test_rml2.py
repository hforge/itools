# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.pdf import (rml2topdf_test, normalize, paragraph_stream,
                        getSampleStyleSheet)
from itools.xml import XMLParser


class FunctionTestCase(unittest.TestCase):

    def test_normalize(self):
        s = ''
        _s = normalize(s)
        self.assertEqual(_s, u'')

        s = ' '
        _s = normalize(s)
        self.assertEqual(_s, u'')

        s = '\t \t   foo \t \t is \t \t \t not \t      \t bar \t \t \t'
        _s = normalize(s)
        self.assertEqual(_s, u'foo is not bar')

        s = 'Hello \t &nbsp; \t Jo'
        _s = normalize(s)
        self.assertEqual(_s, u'Hello &nbsp; Jo')


    def test_formatting(self):
        data = '<p>TXT <i>TEXT<u>TEXT</u></i></p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, 'TXT <i>TEXT<u>TEXT</u></i>')

        data = '<p>TXT <i>TEXT<u>TEXT</u>TEXT</i></p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, 'TXT <i>TEXT<u>TEXT</u>TEXT</i>')

        data = '<p>TXT <i>TEXT<u>TEXT</u></i>TEXT</p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, 'TXT <i>TEXT<u>TEXT</u></i>TEXT')

        data = '<p>TXT <i>TEXT<u>TEXT</u>TEXT</i>TEXT</p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, 'TXT <i>TEXT<u>TEXT</u>TEXT</i>TEXT')

        data = '<p>TXT <i><u>TXT</u></i></p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, 'TXT <i><u>TXT</u></i>')

        data = '<p><i>TEXT<u>TEXT</u></i></p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, '<i>TEXT<u>TEXT</u></i>')

        data = '<p><i>TEXT<u>TEXT</u>TEXT</i></p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, '<i>TEXT<u>TEXT</u>TEXT</i>')

        data = '<p><i>TEXT<u>TEXT</u></i>TEXT</p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, '<i>TEXT<u>TEXT</u></i>TEXT')

        data = '<p><i>TEXT<u>TEXT</u>TEXT</i>TEXT</p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, '<i>TEXT<u>TEXT</u>TEXT</i>TEXT')

        data = '<p><i><u>TXT</u></i></p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, '<i><u>TXT</u></i>')


        data = '<p>TEXT<sup>TEXT</sup></p>'
        stream = XMLParser(data)
        stream.next()
        p = paragraph_stream(stream, 'p', {}, getSampleStyleSheet())
        self.assertEqual(p.text, 'TEXT<super>TEXT</super>')



class HtmlTestCase(unittest.TestCase):

    def test_empty_body(self):
        data = '<html><body></body></html>'
        story, stylesheet = rml2topdf_test(data, raw=True)
        self.assertEqual(len(story), 0)

    def test_paragraph1(self):
        data = '<html><body><p>hello  world</p></body></html>'
        story, stylesheet = rml2topdf_test(data, raw=True)
        self.assertEqual(len(story), 1)

    def test_paragraph2(self):
        data = '<html><body><h1>title</h1><p>hello  world</p>'
        data += '<h2>subtitle1</h2><p>Hello</p><h2>subtitle 2</h2>'
        data += '<p>WORLD     <br/>       </p>;)</body></html>'
        story, stylesheet = rml2topdf_test(data, raw=True)
        self.assertEqual(len(story), 6)

    def test_paragraph3(self):
        story, stylesheet = rml2topdf_test('rml2/paragraph.xml')
        self.assertEqual(len(story), 10)

    def test_list(self):
        story, stylesheet = rml2topdf_test('rml2/list.xml')
        self.assertEqual(len(story), 184)

    def test_image(self):
        data = """
        <html>
            <body>
                <p>hello  world <img src="pdf/itaapy.gif" alt="itaapy" /></p>
                <img src="pdf/itaapy.jpeg" alt="itaapy" />
                <p><img src="pdf/itaapy.png" alt="itaapy" /></p>
            </body>
        </html>"""
        story, stylesheet = rml2topdf_test(data, raw=True)
        self.assertEqual(len(story), 5)


if __name__ == '__main__':
    unittest.main()
