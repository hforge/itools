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
from itools.pdf.pml import Context, normalize, paragraph_stream
from itools.pdf.pml import pmltopdf_test, stl_pmltopdf_test
from itools.pdf.utils import get_color
from itools.vfs import vfs
from itools.xml import XMLParser
from itools.xmlfile import XMLFile


URI = 'http://www.w3.org/1999/xhtml'
NAMESPACES = {None: URI}


######################################################################
# PML part
######################################################################
class pml_FunctionTestCase(unittest.TestCase):

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
        context = Context()
        data = '<p>TXT <i>TEXT<u>TEXT</u></i></p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        self.assertEqual(para.text, '<para>TXT <i>TEXT<u>TEXT</u></i></para>')

        data = '<p>TXT <i>TEXT<u>TEXT</u>TEXT</i></p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        goodanswer = '<para>TXT <i>TEXT<u>TEXT</u>TEXT</i></para>'
        self.assertEqual(para.text, goodanswer)

        data = '<p>TXT <i>TEXT<u>TEXT</u></i>TEXT</p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        goodanswer = '<para>TXT <i>TEXT<u>TEXT</u></i>TEXT</para>'
        self.assertEqual(para.text, goodanswer)

        data = '<p>TXT <i>TEXT<u>TEXT</u>TEXT</i>TEXT</p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        goodanswer = '<para>TXT <i>TEXT<u>TEXT</u>TEXT</i>TEXT</para>'
        self.assertEqual(para.text, goodanswer)

        data = '<p>TXT <i><u>TXT</u></i></p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        self.assertEqual(para.text, '<para>TXT <i><u>TXT</u></i></para>')

        data = '<p><i>TEXT<u>TEXT</u></i></p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        self.assertEqual(para.text, '<para><i>TEXT<u>TEXT</u></i></para>')

        data = '<p><i>TEXT<u>TEXT</u>TEXT</i></p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        self.assertEqual(para.text, '<para><i>TEXT<u>TEXT</u>TEXT</i></para>')

        data = '<p><i>TEXT<u>TEXT</u></i>TEXT</p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        self.assertEqual(para.text, '<para><i>TEXT<u>TEXT</u></i>TEXT</para>')

        data = '<p><i>TEXT<u>TEXT</u>TEXT</i>TEXT</p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        goodanswer = '<para><i>TEXT<u>TEXT</u>TEXT</i>TEXT</para>'
        self.assertEqual(para.text, goodanswer)

        data = '<p><i><u>TXT</u></i></p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        self.assertEqual(para.text, '<para><i><u>TXT</u></i></para>')

        data = '<p>TEXT<sup>TEXT</sup></p>'
        stream = XMLParser(data, NAMESPACES)
        stream.next()
        context.path_on_start_event('p', {})
        para = paragraph_stream(stream, 'p', {}, context)[0]
        self.assertEqual(para.text,
          '<para>TEXT<super><font fontSize="7.2">TEXT</font></super></para>')


    ## FIXME paragraph_stream is buggy
    #def test_formatting_using_span(self):
    #    context = Context()
    #    data = '<p><span style="color: #ff9000">clear syntax</span></p>'
    #    stream = XMLParser(data, NAMESPACES)
    #    stream.next()
    #    context.path_on_start_event('p', {})
    #    para = paragraph_stream(stream, 'p', {}, context)[0]
    #    goodanswer = '<para><font color="#ff9000">clear syntax</font></para>'
    #    self.assertEqual(para.text, goodanswer)

    #    data = '<p>essai<span style="color: rgb(255, 0, 0);"> essai essai'
    #    data += '</span>essai</p>'
    #    stream = XMLParser(data, NAMESPACES)
    #    stream.next()
    #    context.path_on_start_event('p', {})
    #    para = paragraph_stream(stream, 'p', {}, context)[0]
    #    goodanswer = '<para>essai<font color="#ff0000"> essai essai'
    #    goodanswer += '</font>essai</para>'
    #    self.assertEqual(para.text, goodanswer)

    #    data = '<p>essai <span style="color: rgb(0, 255, 0);">essai essai'
    #    data += '</span>essai</p>'
    #    stream = XMLParser(data, NAMESPACES)
    #    stream.next()
    #    context.path_on_start_event('p', {})
    #    para = paragraph_stream(stream, 'p', {}, context)[0]
    #    goodanswer = '<para>essai <font color="#00ff00">essai essai'
    #    goodanswer += '</font>essai</para>'
    #    self.assertEqual(para.text, goodanswer)

    #    data = '<p>essai <span style="color: rgb(0, 0, 255);">essai '
    #    data += 'essai</span> essai</p>'
    #    stream = XMLParser(data, NAMESPACES)
    #    stream.next()
    #    context.path_on_start_event('p', {})
    #    para = paragraph_stream(stream, 'p', {}, context)[0]
    #    goodanswer = '<para>essai <font color="#0000ff">essai essai</font>'
    #    goodanswer += ' essai</para>'
    #    self.assertEqual(para.text, goodanswer)

    #    data = '<p>Span <span style="color: rgb(255, 0, 0);">span    span '
    #    data += '<span style="color: #00DD45;">span</span> span</span>.</p>'
    #    stream = XMLParser(data, NAMESPACES)
    #    stream.next()
    #    context.path_on_start_event('p', {})
    #    para = paragraph_stream(stream, 'p', {}, context)[0]
    #    goodanswer = '<para>Span <font color="#ff0000">span span <font '
    #    goodanswer += 'color="#00dd45">span</font> span</font>.</para>'
    #    self.assertEqual(para.text, goodanswer)



class pml_HtmlTestCase(unittest.TestCase):

    def test_empty_body(self):
        data = '<html><body></body></html>'
        story, stylesheet = pmltopdf_test(data)
        self.assertEqual(len(story), 0)


    def test_paragraph1(self):
        data = '<html><body><p>hello  world</p></body></html>'
        story, stylesheet = pmltopdf_test(data)
        self.assertEqual(len(story), 1)


    def test_paragraph2(self):
        data = '<html><body><h1>title</h1><p>hello  world</p>'
        data += '<h2>subtitle1</h2><p>Hello</p><h2>subtitle 2</h2>'
        data += '<p>WORLD     <br/>       </p>;)</body></html>'
        story, stylesheet = pmltopdf_test(data)
        self.assertEqual(len(story), 6)


    def test_paragraph3(self):
        handler = XMLFile(ref='pml/paragraph.xml')
        story, stylesheet = stl_pmltopdf_test(handler)
        self.assertEqual(len(story), 10)


    def test_paragraph4(self):
        handler = vfs.open('pml/paragraph.xml')
        story, stylesheet = pmltopdf_test(handler)
        self.assertEqual(len(story), 10)


    def test_paragraph_cjk(self):
        handler = vfs.open('pml/paragraph_cjk.xml')
        story, stylesheet = pmltopdf_test(handler)
        self.assertEqual(len(story), 12)


    def test_span(self):
        handler = vfs.open('pml/span.xml')
        story, stylesheet = pmltopdf_test(handler)
        self.assertEqual(len(story), 9)


    def test_list(self):
        handler = XMLFile(ref='pml/list.xml')
        story, stylesheet = stl_pmltopdf_test(handler)
        self.assertEqual(len(story), 163)


    def test_image(self):
        data = """
        <html>
            <body>
                <p>hello  world <img src="pml/itools_powered.gif"
                                     alt="itools" />
                </p>
                <img src="pml/itools_powered.jpeg" alt="itools" />
                <p><img src="pml/itools_powered.png" alt="itools" /></p>
            </body>
        </html>"""
        story, stylesheet = pmltopdf_test(data)
        self.assertEqual(len(story), 3)


    def test_table(self):
        handler = XMLFile(ref='pml/table.xml')
        story, stylesheet = stl_pmltopdf_test(handler, path='pml/table.xml')
        self.assertEqual(len(story), 1)



class pml_ColorTestCase(unittest.TestCase):


    def test_hexa_simple(self):
        str = '#abc'
        color = get_color(str)
        self.assertEqual(color.hexval(), '0xaabbcc')

        str = '#aabbcc'
        color = get_color(str)
        self.assertEqual(color.hexval(), '0xaabbcc')


    def test_name(self):
        for data in (('green', '0x008000'),
                     ('purple', '0x800080'),
                     ('cyan', '0x00ffff')):
            name, expected = data
            color = get_color(name)
            self.assertEqual(color.hexval(), expected)


    def test_rgb(self):
        str = 'rgb(230, 100, 180)'
        color = get_color(str)
        self.assertEqual(color.hexval(), '0xe664b4')


    def test_wrong_color(self):
        str = ''
        color = get_color(str)
        self.assertEqual(color.hexval(), '0x000000')

        str = '#abt'
        color = get_color(str)
        self.assertEqual(color.hexval(), '0x000000')

        str = '#aabbtt'
        color = get_color(str)
        self.assertEqual(color.hexval(), '0x000000')

        str = 'cian'
        color = get_color(str)
        self.assertEqual(color.hexval(), '0x000000')


if __name__ == '__main__':
    unittest.main()
