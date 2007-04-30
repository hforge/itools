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
from itools.pdf.rml import rmltopdf_test, rmltopdf, strip

# Import from the reportlab library
from reportlab.lib.units import inch, cm
from reportlab.platypus.doctemplate import LayoutError

class FunctionTestCase(unittest.TestCase):

    def test_strip(self):
        s = ""
        _s = strip(s)
        self.assertEqual(_s, "")
        
        s = ""
        _s = strip(s, True)
        self.assertEqual(_s, "")
        
        s = " "
        _s = strip(s, True)
        self.assertEqual(_s, " ")


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

    
    #def test_style_sheet_report_lab_exemple(self):
    #    story, stylesheet = rmltopdf_test('pdf/22.xml')


    def test_style_sheet_table_style(self):
        story, stylesheet = rmltopdf_test('pdf/23.xml')
        self.assertRaises(LayoutError, rmltopdf_test, 'pdf/24.xml')

    
    def test_template(self):
        story, stylesheet = rmltopdf_test('pdf/25.xml')
        

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



if __name__ == '__main__':
    unittest.main()
