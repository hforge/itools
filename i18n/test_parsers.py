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


# Python
import unittest
from unittest import TestCase, TestSuite, TextTestRunner

# itools
import parsers



class POTestCase(TestCase):
    def test_case1(self):
        """Test for newlines."""
        content = 'msgid "Add"\n' \
                  'msgstr "Añadir\\n"\n'

        po = parsers.PO(content)
        assert po.messages == {('Add',): ([], ['Añadir\n'])}


    def test_case2(self):
        """Test for multiple lines"""
        content = 'msgid "Hello world"\n' \
                  'msgstr ""\n' \
                  '"Hola "\n' \
                  '"mundo"\n'

        po = parsers.PO(content)
        assert po.messages == {('Hello world',): ([], ['', 'Hola ', 'mundo'])}


    def test_case3(self):
        """Test for double quotes."""
        content = 'msgid "test"\n' \
                  'msgstr "Esto es una \\"prueba\\""\n'

        po = parsers.PO(content)
        assert po.messages == {('test',): ([], ['Esto es una "prueba"'])}


    def test_output(self):
        """Test output"""
        content = '# Comment\n' \
                  'msgid "Hello"\n' \
                  'msgstr ""\n' \
                  '"Hola\\n"\n'

        po = parsers.PO(content)
        assert po.write() == content


class XHMLTestCase(TestCase):
    def test_case1(self):
        """Test element content."""
        data = '<p>hello world</p>'

        xhtml = parsers.XHTML(data)
        messages = xhtml.get_messages()

        assert messages == [u'hello world']


    def test_case2(self):
        """Test simple attribute."""
        data = '<img alt="The beach" src="beach.jpg" />'

        xhtml = parsers.XHTML(data)
        messages = xhtml.get_messages()

        assert messages == [u'The beach']


    def test_case3(self):
        """Test complex attribute."""
        data = '<html>\n' \
               '<input type="text" name="id" />\n' \
               '<input type="submit" value="Change" />\n' \
               '</html>'

        xhtml = parsers.XHTML(data)
        messages = xhtml.get_messages()

        assert messages == [u'Change']


    def test_case4(self):
        """Test translation of an element content"""
        html = '<p>hello world</p>'
        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"'

        xhtml = parsers.XHTML(html)
        data = xhtml.translate(po)

        assert data == '<p>hola mundo</p>'


    def test_case5(self):
        """Test translation of an element content"""
        html = '<img alt="The beach" src="beach.jpg" />'
        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'

        xhtml = parsers.XHTML(html)
        data = xhtml.translate(po)

        assert data == '<img src="beach.jpg" alt="La playa"></img>'


    def test_case6(self):
        """Test translation of an element content"""
        html = '<html>\n' \
               '<input type="text" name="id" />\n' \
               '<input type="submit" value="Change" />\n' \
               '</html>'
        po = 'msgid "Change"\n' \
             'msgstr "Cambiar"'

        xhtml = parsers.XHTML(html)
        data = xhtml.translate(po)

        assert data == '<html>\n' \
               '<input type="text" name="id"></input>\n' \
               '<input type="submit" value="Cambiar"></input>\n' \
               '</html>'


class HMLTestCase(TestCase):
    def test_case1(self):
        """Test element content."""
        data = '<p>hello world</p>'

        html = parsers.HTML(data)
        messages = html.get_messages()

        assert messages == [u'hello world']


    def test_case2(self):
        """Test simple attribute."""
        data = '<img alt="The beach" src="beach.jpg">'

        html = parsers.HTML(data)
        messages = html.get_messages()

        assert messages == [u'The beach']


    def test_case3(self):
        """Test complex attribute."""
        data = '<html>\n' \
               '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">\n' \
               '</html>'

        html = parsers.HTML(data)
        messages = html.get_messages()

        assert messages == [u'Change']


    def test_case4(self):
        """Test translation of an element content"""
        html = '<p>hello world</p>'
        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"'

        html = parsers.HTML(html)
        data = html.translate(po)

        assert data == '<p>hola mundo</p>'


    def test_case5(self):
        """Test translation of an element content"""
        html = '<img alt="The beach" src="beach.jpg">'
        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'

        html = parsers.HTML(html)
        data = html.translate(po)

        assert data == '<img src="beach.jpg" alt="La playa">'


    def test_case6(self):
        """Test translation of an element content"""
        html = '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">'
        po = 'msgid "Change"\n' \
             'msgstr "Cambiar"'

        html = parsers.HTML(html)
        data = html.translate(po)

        assert data == '<input type="text" name="id">\n' \
               '<input type="submit" value="Cambiar">'





if __name__ == '__main__':
    unittest.main()
