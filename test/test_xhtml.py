# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2004 J. David Ibáñez <jdavid@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools
from itools.xhtml import XHTML
from itools.gettext import PO



class SegmentationTestCase(TestCase):

    def test_paragraph(self):
        """Test formatted paragraph"""
        data = '<p xmlns="http://www.w3.org/1999/xhtml">\n' \
               'The Mozilla project maintains <em>choice</em> and\n' \
               '<em>innovation</em> on the Internet. Developing the\n' \
               'acclaimed, <em>open source</em>, <b>Mozilla 1.6</b>.\n' \
               '</p>'
        doc = XHTML.Document()
        doc.load_state_from_string(data)

        messages = list(doc.get_messages())
        expected = [(u'The Mozilla project maintains <em>choice</em> and'
                     u' <em>innovation</em> on the Internet.', 0),
                    (u'Developing the acclaimed, <em>open source</em>,'
                     u' <b>Mozilla 1.6</b>.', 0)]
        self.assertEqual(messages, expected)


    def test_table(self):
        data = '<table xmlns="http://www.w3.org/1999/xhtml">\n' \
               '  <tr>\n' \
               '    <th>Title</th>\n' \
               '    <th>Size</th>\n' \
               '  </tr>\n' \
               '  <tr>\n' \
               '    <td>The good, the bad and the ugly</td>\n' \
               '    <td>looong</td>\n' \
               '  </tr>\n' \
               '  <tr>\n' \
               '    <td>Love story</td>\n' \
               '    <td>even longer</td>\n' \
               '  </tr>\n' \
               '</table>'
        doc = XHTML.Document()
        doc.load_state_from_string(data)

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
        data = '<body xmlns="http://www.w3.org/1999/xhtml">\n' \
               '  <p>this <em>word</em> is nice</p>\n' \
               '  <a href="/"><img src="logo.png" /></a>\n' \
               '  <p><em>hello world</em></p><br/>' \
               '  bye <em>J. David Ibanez Palomar</em>\n' \
               '</body>'
        doc = XHTML.Document()
        doc.load_state_from_string(data)

        messages = list(doc.get_messages())
        expected = [(u'this <em>word</em> is nice', 0),
                    (u'hello world', 0),
                    (u'<br/> bye <em>J. David Ibanez Palomar</em>', 0)]
        self.assertEqual(messages, expected)


    def test_form(self):
        """Test complex attribute."""
        # The document
        data = '<form xmlns="http://www.w3.org/1999/xhtml">\n' \
               '  <input type="text" name="id" />\n' \
               '  <input type="submit" value="Change" />\n' \
               '</form>'
        doc = XHTML.Document()
        doc.load_state_from_string(data)

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'Change', 0)])



class TranslationTestCase(TestCase):

    def setUp(self):
        template ="""<?xml version="1.0" encoding="UTF-8"?>
                     <!DOCTYPE html
                      PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
                      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
                      <html xmlns="http://www.w3.org/1999/xhtml"
                      xmlns:stl="http://xml.itools.org/namespaces/stl">
                     <head></head>
                      <body>%s</body>
                     </html>
                  """
        self.template = template
  
              
    def test_case1(self):
        """Test element content."""
        data = self.template % '<p>hello litle world</p>'
        doc = XHTML.Document()
        doc.load_state_from_string(data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'hello litle world', 0)])


    def test_case2(self):
        """Test simple attribute."""
        data = self.template % '<img alt="The beach" src="beach.jpg" />' 
        doc = XHTML.Document()
        doc.load_state_from_string(data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'The beach', 0)])


    def test_case3(self):
        """Test complex attribute."""
        data = self.template % """<input type="text" name="id" />
                                  <input type="submit" value="Change" />""" 
        doc = XHTML.Document()
        doc.load_state_from_string(data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'Change', 0)])


    def test_case4(self):
        """Test translation of an element content"""
        html = self.template % '<p>hello world</p>'

        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"\n'

        p = PO()
        p.load_state_from_string(po)
        xhtml = XHTML.Document()
        xhtml.load_state_from_string(html)

        html = xhtml.translate(p)
        xhtml = XHTML.Document()
        xhtml.load_state_from_string(html)
        
        messages = list(xhtml.get_messages())
        self.assertEqual(messages, [(u'hola mundo', 0)])


    def test_case5(self):
        """Test translation of an element content"""
        html =  self.template  % '<img alt="The beach" src="beach.jpg" />'
        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'

        p = PO()
        p.load_state_from_string(po)
        xhtml = XHTML.Document()
        xhtml.load_state_from_string(html)

        html = xhtml.translate(p)
        xhtml = XHTML.Document()
        xhtml.load_state_from_string(html)

        messages = list(xhtml.get_messages())
        self.assertEqual(messages, [(u'La playa', 0)])



if __name__ == '__main__':
    unittest.main()
