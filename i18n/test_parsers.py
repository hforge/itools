# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2001, 2002 J. David Ibáñez <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from Python
import unittest
from unittest import TestCase, TestSuite, TextTestRunner

# Import from itools
import parsers
from itools.resources import memory


import os


class POTestCase(TestCase):

    def test_case1(self):
        """Test for newlines."""
        content = ["# SOME DESCRIPTIVE TITLE.",
                   "# Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER",
                   "# This file is distributed under the same license as the PACKAGE package.",
                   "# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.",
                   "#",
                   "#, fuzzy",
                   'msgid "Add"',
                   'msgstr "Anadir\\n"']
        content = '\n'.join(content)
                  
        po = parsers.PO
        content = memory.File(content)
        p =  po.PO(content)
        assert p.messages[0].msgid == ['Add']
        assert p.messages[0].msgstr[0] == 'Anadir\n'
        

    def test_case2(self):
        """Test for multiple lines"""
        content = 'msgid "Hello world"\n' \
                  'msgstr ""\n' \
                  '"Hola "\n' \
                  '"mundo"\n'

        po = parsers.PO
        content = memory.File(content)
        p = po.PO(content)
        assert p.messages[0].msgid == ['Hello world']
        assert p.messages[0].msgstr == [u'', u'Hola ', u'mundo']


    def test_case3(self):
        """Test for double quotes."""
        content = 'msgid "test"\n' \
                  'msgstr "Esto es una \\"prueba\\""\n'

        p = parsers.PO.PO(memory.File(content))
        assert p.messages[0].msgid == ['test']
        assert p.messages[0].msgstr == [u'Esto es una "prueba"']


    def test_output(self):
        """Test output"""
        content = '# Comment\n' \
                  'msgid "Hello"\n' \
                  'msgstr ""\n' \
                  '"Hola\\n"\n'

        p = parsers.PO.PO(memory.File(content))
        assert p.messages[0].msgid == ['Hello']
        assert p.messages[0].msgstr == [u'', u'Hola\n']



class XHMLTestCase(TestCase):

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
        data = memory.File(data)
        xhtml = parsers.XHTML.Document(data)
        messages = list(xhtml.get_messages())

        assert messages == [u'hello litle world']


    def test_case2(self):
        """Test simple attribute."""
        data = self.template % '<img alt="The beach" src="beach.jpg" />' 
        data = memory.File(data)
        xhtml = parsers.XHTML.Document(data)
        messages = list(xhtml.get_messages())

        assert messages == [u'The beach']


    def test_case3(self):
        """Test complex attribute."""
        data = self.template % """<input type="text" name="id" />
                                  <input type="submit" value="Change" />""" 
        data = memory.File(data)
        xhtml = parsers.XHTML.Document(data)
        messages = list(xhtml.get_messages())

        assert messages == [u'Change']


    def test_case4(self):
        """Test translation of an element content"""
        html = self.template % '<p>hello world</p>'

        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"\n'

        p = parsers.PO.PO(memory.File(po))
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)

        html = xhtml.translate(p)
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)
        
        data = list(xhtml.get_messages())
        assert data == [u'hola mundo']


    def test_case5(self):
        """Test translation of an element content"""
        html =  self.template  % '<img alt="The beach" src="beach.jpg" />'
        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'

        p = parsers.PO.PO(memory.File(po))
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)

        html = xhtml.translate(p)
        html = memory.File(html)
        xhtml = parsers.XHTML.Document(html)

        data = list(xhtml.get_messages())
        assert data == [u'La playa']



class HMLTestCase(TestCase):
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
