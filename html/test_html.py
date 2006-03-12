# -*- coding: ISO-8859-1 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools
from itools.resources import memory
import HTML


class HMLTestCase(TestCase):

    def test_case1(self):
        """Test element content."""
        data = '<p>hello world</p>'
        resource = memory.File(data)
        doc = HTML.Document(resource)

        self.assertEqual(doc.get_messages(), [u'hello world'])


    def test_case2(self):
        """Test simple attribute."""
        data = '<img alt="The beach" src="beach.jpg">'
        resource = memory.File(data)
        doc = HTML.Document(resource)

        self.assertEqual(doc.get_messages(), [u'The beach'])


    def test_case3(self):
        """Test complex attribute."""
        data = '<html>\n' \
               '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">\n' \
               '</html>'
        resource = memory.File(data)
        doc = HTML.Document(resource)

        self.assertEqual(doc.get_messages(), [u'Change'])


    def test_case4(self):
        """Test translation of an element content"""
        html = '<p>hello world</p>'
        resource = memory.File(data)
        doc = HTML.Document(resource)

        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"'
        self.assertEqual(doc.translate(po),
                         '<p>hola mundo</p>')


    def test_case5(self):
        """Test translation of an element content"""
        data = '<img alt="The beach" src="beach.jpg">'
        resource = memory.File(data)
        doc = HTML.Document(resource)

        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'
        self.assertEqual(doc.translate(po),
                         '<img src="beach.jpg" alt="La playa">')


    def test_case6(self):
        """Test translation of an element content"""
        data = '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">'
        resource = memory.File(data)
        doc = HTML.Document(resource)

        po = 'msgid "Change"\n' \
             'msgstr "Cambiar"'
        self.assertEqual(doc.translate(po),
                         '<input type="text" name="id">\n' \
                         '<input type="submit" value="Cambiar">')



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
        html = self.template % '<p>hello world</p>'
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)
        messages = list(xhtml.get_messages())
        assert messages == [u'hello world']


    def test_case2(self):
        """Test simple attribute."""
        html = self.template % '<img alt="The beach" src="beach.jpg"/>'
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)
        messages = list(xhtml.get_messages())
        assert messages == [u'The beach']


    def test_case3(self):
        """Test complex attribute."""
        html = self.template % '<input type="text" name="id"/>\n' \
                               '<input type="submit" value="Change"/>\n'
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)
        messages = list(xhtml.get_messages())
        assert messages == [u'Change']


    def test_case4(self):
        """Test translation of an element content"""
        html = self.template % '<p>hello world</p>'
        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"'
         
        p = parsers.PO.PO(memory.File(po))
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)
        
        html = xhtml.translate(p)
        result = self.template % '<p>hola mundo </p>'
        assert html == result
        

    def test_case5(self):
        """Test translation of an element content"""
        html = '<img alt="The beach" src="beach.jpg"/>'
        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'


        p = parsers.PO.PO(memory.File(po))
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)
         
        #print '-----------------', xhtml
        #html = xhtml.translate(p)
        #result = self.template % '<img src="beach.jpg" alt="La playa">'
        #assert html == result



    def test_case6(self):
        """Test translation of an element content"""
        html = self.template % '<input type="text" name="id"/>\n' \
                               '<input type="submit" value="Change"/>'
        po = 'msgid "Change"\n' \
             'msgstr "Cambiar"'

        p = parsers.PO.PO(memory.File(po))
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)
  
        html = xhtml.translate(p)
        result = self.template % '<input type="text" name="id"/>\n' \
                                 '<input type="submit" value="Cambiar/">'

        assert html == result




if __name__ == '__main__':
    unittest.main()
