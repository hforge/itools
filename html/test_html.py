# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2004 J. David Ibáñez <jdavid@itaapy.com>
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




if __name__ == '__main__':
    unittest.main()
