# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2004, 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
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
from itools.xml import stream_to_str, START_ELEMENT, END_ELEMENT
from itools.html import HTMLFile, Parser
from itools.gettext import PO


def parse_tags(data):
    return [ (type, value[1]) for type, value, line in Parser(data)
             if type == START_ELEMENT or type == END_ELEMENT ]


class ParserTestCase(TestCase):

    def test_doctype(self):
        data = '<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">'
        stream = Parser(data)
        self.assertEqual(stream_to_str(stream), data)


    def test_obvious(self):
        data = '<p></p>'
        expected = [(START_ELEMENT, 'p'), (END_ELEMENT, 'p')]
        self.assertEqual(parse_tags(data), expected)


    def test_empty(self):
        data = '<br>'
        expected = [(START_ELEMENT, 'br'), (END_ELEMENT, 'br')]
        self.assertEqual(parse_tags(data), expected)


    def test_ul(self):
        data = '<ul><li><li></li></ul>'
        expected = [
            (START_ELEMENT, 'ul'), (START_ELEMENT, 'li'), (END_ELEMENT, 'li'),
            (START_ELEMENT, 'li'), (END_ELEMENT, 'li'), (END_ELEMENT, 'ul')]
        self.assertEqual(parse_tags(data), expected)


    def test_forbidden(self):
        data = '<html><body><title></title></body></html>'
        expected = [
            (START_ELEMENT, 'html'), (START_ELEMENT, 'body'),
            (START_ELEMENT, 'title'), (END_ELEMENT, 'title'),
            (END_ELEMENT, 'body'), (END_ELEMENT, 'html')]
        self.assertEqual(parse_tags(data), expected)





class i18nTestCase(TestCase):

    def test_case1(self):
        """Test element content."""
        doc = HTMLFile(string=
            '<p>hello world</p>')

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'hello world', 0)])


    def test_case2(self):
        """Test simple attribute."""
        doc = HTMLFile(string=
            '<img alt="The beach" src="beach.jpg">')

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'The beach', 0)])


    def test_case3(self):
        """Test complex attribute."""
        doc = HTMLFile(string=
            '<html>\n'
            '<input type="text" name="id">\n'
            '<input type="submit" value="Change">\n'
            '</html>')

        messages = list(doc.get_messages())
        self.assertEqual(messages, [(u'Change', 0)])


    def test_case4(self):
        """Test translation of an element content"""
        doc = HTMLFile(string=
            '<p>hello world</p>')

        p = PO(string=
            'msgid "hello world"\n'
            'msgstr "hola mundo"')

        self.assertEqual(doc.translate(p), '<p>hola mundo</p>')


    def test_case5(self):
        """Test translation of an element content"""
        doc = HTMLFile(string=
            '<img alt="The beach" src="beach.jpg">')

        po = PO(string=
            'msgid "The beach"\n'
             'msgstr "La playa"')

        string = doc.translate(po)
        output = HTMLFile(string=string)

        expected = HTMLFile(string=
            '<img alt="La playa" src="beach.jpg">')
        self.assertEqual(output, expected)


    def test_case6(self):
        """Test translation of an element content"""
        doc = HTMLFile(string=
            '<input type="text" name="id">\n'
            '<input type="submit" value="Change">')

        p = PO(string=
            'msgid "Change"\n'
            'msgstr "Cambiar"')

        output = HTMLFile(string=doc.translate(p))

        expected = HTMLFile(string=
            '<input type="text" name="id">\n'
            '<input type="submit" value="Cambiar">')
        self.assertEqual(output, expected)



if __name__ == '__main__':
    unittest.main()
