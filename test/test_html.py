# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2004 J. David Ibáñez <jdavid@itaapy.com>
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
from unittest import TestCase

# Import from itools
from itools.html import Document
from itools.gettext import PO


class HTMLTestCase(TestCase):

    def test_case1(self):
        """Test element content."""
        doc = Document(string=
            '<p>hello world</p>')

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'hello world', 0)])


    def test_case2(self):
        """Test simple attribute."""
        doc = Document(string=
            '<img alt="The beach" src="beach.jpg">')

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'The beach', 0)])


    def test_case3(self):
        """Test complex attribute."""
        doc = Document(string=
            '<html>\n'
            '<input type="text" name="id">\n'
            '<input type="submit" value="Change">\n'
            '</html>')

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'Change', 0)])


    def test_case4(self):
        """Test translation of an element content"""
        doc = Document(string=
            '<p>hello world</p>')

        p = PO(string=
            'msgid "hello world"\n'
            'msgstr "hola mundo"')

        self.assertEqual(doc.translate(p), '<p>hola mundo</p>')


    def test_case5(self):
        """Test translation of an element content"""
        doc = Document(string=
            '<img alt="The beach" src="beach.jpg">')

        po = PO(string=
            'msgid "The beach"\n'
             'msgstr "La playa"')

        string = doc.translate(po)
        output = Document(string=string)

        expected = Document(string=
            '<img alt="La playa" src="beach.jpg">')
        self.assertEqual(output, expected)


    def test_case6(self):
        """Test translation of an element content"""
        doc = Document(string=
            '<input type="text" name="id">\n'
            '<input type="submit" value="Change">')

        p = PO(string=
            'msgid "Change"\n'
            'msgstr "Cambiar"')

        output = Document(string=doc.translate(p))

        expected = Document(string=
            '<input type="text" name="id">\n'
            '<input type="submit" value="Cambiar">')
        self.assertEqual(output, expected)



if __name__ == '__main__':
    unittest.main()
