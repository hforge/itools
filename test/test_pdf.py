# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import os
import sys
import unittest

# Import from itools
from itools.pdf import rmltopdf
from itools.pdf.rml import rmltopdf_test, normalize, stream_next, \
                           get_color, get_page_size_orientation
from itools.xml import Parser, START_ELEMENT, END_ELEMENT, TEXT

# Import from the reportlab library
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.colors import Color, CMYKColor
from reportlab.lib.pagesizes import landscape, portrait

from reportlab.platypus.doctemplate import LayoutError


class FunctionTestCase(unittest.TestCase):

    def test_normalize(self):
        s = u''
        _s = normalize(s)
        self.assertEqual(_s, u'')
        
        s = u''
        _s = normalize(s, True)
        self.assertEqual(_s, u'')
        
        s = u' '
        _s = normalize(s, True)
        self.assertEqual(_s, u' ')

        s = u'\t \t   foo \t \t is \t \t \t not \t      \t bar \t \t \t'
        _s = normalize(s, False)
        self.assertEqual(_s, u'foo is not bar')
        _s = normalize(s, True)
        self.assertEqual(_s, u' foo is not bar ')


    def test_stream_next(self):
        xml = '<document><foo at="bar">foo content</foo><table><tr bg="red">'
        xml += '<td>cell1</td></tr></table>'
        xml += '<para aligment="left">para content</para></document>'

        stream = Parser(xml)
        # <document>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name, attributes = value
        self.assertEqual(event, START_ELEMENT)
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'document')
        self.assertEqual(attributes, {})

        # <foo at="bar">
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name, attributes = value
        self.assertEqual(event, START_ELEMENT)
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'foo')
        self.assertEqual(attributes, {(None, 'at'): 'bar'})

        # content
        event, value, line_number = stream_next(stream)
        self.assertEqual(value, 'foo content')

        # </foo>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'foo')

        # <table>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name, attributes = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(event, START_ELEMENT)
        self.assertEqual(tag_name, 'table')
        self.assertEqual(attributes, {})

        # <tr>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name, attributes = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(event, START_ELEMENT)
        self.assertEqual(tag_name, 'tr')
        self.assertEqual(attributes, {(None, 'bg'): 'red'})

        # <td>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name, attributes = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(event, START_ELEMENT)
        self.assertEqual(tag_name, 'td')
        self.assertEqual(attributes, {})

        # cell1
        event, value, line_number = stream_next(stream)
        self.assertEqual(event, TEXT)
        self.assertEqual(value, 'cell1')

        # </td>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'td')

        # </tr>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'tr')

        # </table>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'table')

        # <para>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name, attributes = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(event, START_ELEMENT)
        self.assertEqual(tag_name, 'para')
        self.assertEqual(attributes, {(None, 'aligment'): 'left'})

        # para content
        event, value, line_number = stream_next(stream)
        self.assertEqual(event, TEXT)
        self.assertEqual(value, 'para content')

        # </para>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'para')

        # </document>
        event, value, line_number = stream_next(stream)
        tag_uri, tag_name = value
        self.assertEqual(tag_uri, None)
        self.assertEqual(tag_name, 'document')

    
    def test_get_color(self):
        black = Color(0, 0, 0)
        color = get_color('teal')
        rgb1 = color.rgb()
        rgb2 = getattr(colors, 'teal').rgb()
        self.assertEqual(rgb1, rgb2)

        color = get_color('teal55')
        self.assertEqual(color.rgb(), black.rgb())

        color = get_color('(1, 0, 1)')
        self.assertEqual(color.rgb(), (1.0, 0.0, 1.0))
        
        color = get_color('[1,0,0,0]')
        cmyk_color = CMYKColor(1, 0, 0, 0)
        self.assertEqual(color.rgb(), cmyk_color.rgb())
        
        color = get_color('[1,0]')
        self.assertEqual(color.rgb(), black.rgb())

        color = get_color("PCMYKColor(0,50,85,20,spotName='PANTONE 288 CV')")
        self.assertEqual(color.rgb(), black.rgb())


    def test_get_page_size_orientation(self):
        content = '(176mm,297mm)'
        orienter, data = get_page_size_orientation(content)
        self.assertEqual(type(orienter), type(portrait))
        self.assertEqual(data, content)

        content = '(176 mm, 297 mm)'
        orienter, data = get_page_size_orientation(content)
        self.assertEqual(type(orienter), type(portrait))
        self.assertEqual(data, content)

        content = '(176 mm, 297 mm)'
        orienter, data = get_page_size_orientation('landscape %s' % content)
        self.assertEqual(type(orienter), type(landscape))
        self.assertEqual(data.strip(), content)
        
        content = '(176 mm, 297 mm)'
        orienter, data = get_page_size_orientation('%s landscape' % content)
        self.assertEqual(type(orienter), type(landscape))
        self.assertEqual(data.strip(), content)
    
        content = 'A4'
        orienter, data = get_page_size_orientation('%s landscape' % content)
        self.assertEqual(type(orienter), type(landscape))
        self.assertEqual(data.strip(), content)
        
        content = 'A3'
        orienter, data = get_page_size_orientation('%s' % content)
        self.assertEqual(type(orienter), type(portrait))
        self.assertEqual(data.strip(), content)
        
        content = '176 mm, 297 mm'
        orienter, data = get_page_size_orientation('%s landscape' % content)
        self.assertEqual(type(orienter), type(landscape))
        self.assertEqual(data.strip(), content)

        content = 'letter'
        orienter, data = get_page_size_orientation('%s' % content)
        self.assertEqual(type(orienter), type(portrait))
        self.assertEqual(data.strip(), content)


class DocumentTestCase(unittest.TestCase):
    
    def test_no_story(self):
        story, stylesheet = rmltopdf_test('pdf/01.xml')
        self.assertEqual(len(story), 0)


class StylesheetTestCase(unittest.TestCase):

    def test_style_sheet_empty(self):
        story, stylesheet = rmltopdf_test('pdf/20.xml')
    

    def test_style_sheet_para_style(self):
        story, stylesheet = rmltopdf_test('pdf/21.xml')

        style = stylesheet['h1']
        self.assertEqual(style.name, 'Heading1')
        self.assertEqual(style.fontName, 'Courier-Bold')
        self.assertEqual(style.fontSize, 12)
        self.assertEqual(style.spaceBefore, 0.5 * cm)

        style = stylesheet['style1']
        self.assertEqual(style.fontName, 'Courier')
        self.assertEqual(style.fontSize, 10)

        style = stylesheet['style2']
        self.assertEqual(style.parent, stylesheet['style1'])
        self.assertEqual(style.leftIndent, 1 * inch)

        style = stylesheet['style7']
        self.assertEqual(style.parent, stylesheet['style1'])
        self.assertEqual(style.leading, 15)
        self.assertEqual(style.leftIndent, 1 * inch)
        self.assertEqual(style.rightIndent, 1 * inch)

    
    def test_style_sheet_report_lab_exemple(self):
        story, stylesheet = rmltopdf_test('pdf/22.xml')


    def test_style_sheet_table_style(self):
        story, stylesheet = rmltopdf_test('pdf/23.xml')
        self.assertRaises(LayoutError, rmltopdf_test, 'pdf/24.xml')

    
    def test_template(self):
        story, stylesheet = rmltopdf_test('pdf/25.xml')
        content = rmltopdf('pdf/25.xml')
        f = open('pdf/25.pdf', 'w')
        f.write(content)
        f.close()


    def test_alias(self):
        story, stylesheet = rmltopdf_test('pdf/27.xml')
        self.assertEqual(len(story), 6)
        self.assertEqual(story[0].style.parent.name, 'BodyText')
        self.assertEqual(story[1].style.parent.name, 'Normal')
        self.assertEqual(story[2].style.parent.name, 'Heading1')
        self.assertEqual(story[3].style.parent.name, 'Heading1')
        self.assertEqual(story[4].style.parent.name, 'Normal')
        self.assertEqual(story[5].style.parent.name, 'Heading1')


    def test_pagesizes(self):
        filename = 'pdf/28_'
        for type in ['A', 'B']:
            for size in range(0, 7):
                temp = 'pdf/28_%s%s.xml' % (type, size)
                content = rmltopdf(temp)
                f = open('%s.pdf' % temp, 'w')
                f.write(content)
                f.close()
       

class StoryTestCase(unittest.TestCase):
    
    def test_raw(self):
        story, stylesheet = rmltopdf_test('pdf/02.xml')
        self.assertEqual(len(story), 0)


    def test_heading(self):
        story, stylesheet = rmltopdf_test('pdf/03.xml')
        self.assertEqual(len(story), 3)


    def test_pre(self):
        story, stylesheet = rmltopdf_test('pdf/04.xml')
        self.assertEqual(len(story), 5)
    

    def test_para(self):
        story, stylesheet = rmltopdf_test('pdf/06.xml')
        self.assertEqual(len(story), 6)
    

    def test_spacer(self):
        story, stylesheet = rmltopdf_test('pdf/07.xml')
        self.assertEqual(len(story), 2)


    def test_spacer_not_valid(self):
        story, stylesheet = rmltopdf_test('pdf/08.xml')
        self.assertEqual(len(story), 0)


    def test_keepinframe(self):
        content = rmltopdf('pdf/26.xml')
        f = open('pdf/26.pdf', 'w')
        f.write(content)
        f.close()
              
              
class ImageTestCase(unittest.TestCase):
             
    def test_image(self):
        story, stylesheet = rmltopdf_test('pdf/05.xml')
        self.assertEqual(len(story), 9)


class TableTestCase(unittest.TestCase):

    def test_little(self):
        story, stylesheet = rmltopdf_test('pdf/10.xml')
        self.assertEqual(len(story), 1)


    def test_error(self):
        self.assertRaises(ValueError, rmltopdf_test, 'pdf/11.xml')


    def test_big(self):
        story, stylesheet = rmltopdf_test('pdf/12.xml')
        self.assertEqual(len(story), 1)


    def test_inner_widget(self):
        story, stylesheet = rmltopdf_test('pdf/13.xml')
        self.assertEqual(len(story), 1)
    

    def test_inner_table(self):
        story, stylesheet = rmltopdf_test('pdf/14.xml')
        self.assertEqual(len(story), 1)


    def test_td_attributes(self):
        content = rmltopdf('pdf/15.xml')
        f = open('pdf/15.xml.pdf', 'w')
        f.write(content)
        f.close()


class GlobalTestCase(unittest.TestCase):

    def test_global(self):
        content = rmltopdf('pdf/global.xml')
        f = open('pdf/global.pdf', 'w')
        f.write(content)
        f.close()


if __name__ == '__main__':
    unittest.main()
