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
from itools.html import Document
from itools.gettext import PO


class HTMLTestCase(TestCase):

    def test_case1(self):
        """Test element content."""
        data = '<p>hello world</p>'
        doc = Document()
        doc.load_state_from_string(data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'hello world', 0)])


    def test_case2(self):
        """Test simple attribute."""
        data = '<img alt="The beach" src="beach.jpg">'
        doc = Document()
        doc.load_state_from_string(data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'The beach', 0)])


    def test_case3(self):
        """Test complex attribute."""
        data = '<html>\n' \
               '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">\n' \
               '</html>'
        doc = Document()
        doc.load_state_from_string(data)
        messages = list(doc.get_messages())

        self.assertEqual(messages, [(u'Change', 0)])


    def test_case4(self):
        """Test translation of an element content"""
        data = '<p>hello world</p>'
        doc = Document()
        doc.load_state_from_string(data)

        po = 'msgid "hello world"\n' \
             'msgstr "hola mundo"'
        p = PO()
        p.load_state_from_string(po)

        self.assertEqual(doc.translate(p), '<p>hola mundo</p>')


    def test_case5(self):
        """Test translation of an element content"""
        data = '<img alt="The beach" src="beach.jpg">'
        doc = Document()
        doc.load_state_from_string(data)

        po = 'msgid "The beach"\n' \
             'msgstr "La playa"'
        p = PO()
        p.load_state_from_string(po)

        self.assertEqual(doc.translate(p),
                         '<img src="beach.jpg" alt="La playa">')


    def test_case6(self):
        """Test translation of an element content"""
        data = '<input type="text" name="id">\n' \
               '<input type="submit" value="Change">'
        doc = Document()
        doc.load_state_from_string(data)

        po = 'msgid "Change"\n' \
             'msgstr "Cambiar"'
        p = PO()
        p.load_state_from_string(po)

        self.assertEqual(doc.translate(p),
                         '<input type="text" name="id">\n' \
                         '<input type="submit" value="Cambiar">')



if __name__ == '__main__':
    unittest.main()
