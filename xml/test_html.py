# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002, 2003 J. David Ibáñez <jdavid@itaapy.com>
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
from sets import Set
import unittest
from unittest import TestCase

# Import from itools.handlers
import HTML


class HMLTestCase(TestCase):
    def test_case1(self):
        """Test element content."""
        data = '<p>hello world</p>'

        html = HTML.Document(data)
        messages = html.get_messages()

        assert messages == Set([u'hello world'])


    def test_case2(self):
        """Test simple attribute."""
        data = '<img alt="The beach" src="beach.jpg">'

        html = HTML.Document(data)
        messages = html.get_messages()

        assert messages == Set([u'The beach'])


    def test_case3(self):
        """Test complex attribute."""
        data = '<html>\n' \
               '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">\n' \
               '</html>'

        html = HTML.Document(data)
        messages = html.get_messages()

        assert messages == Set([u'Change'])


    def test_case4(self):
        """Test translation of an element content"""
        html = '<p>hello world</p>'
        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"'

        html = HTML.Document(html)
        data = html.translate(po)

        assert data == '<p>hola mundo</p>'


    def test_case5(self):
        """Test translation of an element content"""
        html = '<img alt="The beach" src="beach.jpg">'
        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'

        html = HTML.Document(html)
        data = html.translate(po)

        assert data == '<img src="beach.jpg" alt="La playa">'


    def test_case6(self):
        """Test translation of an element content"""
        html = '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">'
        po = 'msgid "Change"\n' \
             'msgstr "Cambiar"'

        html = HTML.Document(html)
        data = html.translate(po)

        assert data == '<input type="text" name="id">\n' \
               '<input type="submit" value="Cambiar">'




if __name__ == '__main__':
    unittest.main()
