# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.handlers import get_handler
from itools.stl import stl
from itools.stl.stl import NamespaceStack, substitute, evaluate
from itools.xml import Document
import itools.xhtml


class SubstituteTestCase(unittest.TestCase):

    def setUp(self):
        namespace = {'name': u'Toto'}

        self.stack = NamespaceStack()
        self.stack.append(namespace)
        self.repeat = NamespaceStack()


    def test_simple(self):
        data = 'Hello ${name}'
        expected = 'Hello Toto', 1

        output = substitute(data, self.stack, self.repeat)
        self.assertEqual(output, expected)



class STLTestCase(unittest.TestCase):

    def test_none(self):
        stack = NamespaceStack()
        stack.append({})
        repeat = NamespaceStack()

        expression = evaluate('none', stack, repeat)
        self.assertEqual(expression, None)


    def test_traversal(self):
        namespace = {'a': {'b': {'c': 'hello world'}}}
        stack = NamespaceStack()
        stack.append(namespace)
        repeat = NamespaceStack()

        value = evaluate('a/b/c', stack, repeat)
        self.assertEqual(value, 'hello world')


    def test_attribute(self):
        handler = Document(string=
            '<img xmlns="http://www.w3.org/1999/xhtml" border="${border}" />')

        namespace = {'border': 5}
        output = stl(handler, namespace)
        self.assert_('border="5"' in output)


    def test_attribute_accent(self):
        handler = Document(string=
            '<input xmlns="http://www.w3.org/1999/xhtml" value="${name}" />')

        namespace = {'name': u'étoile'}
        output = stl(handler, namespace)
        self.assert_('value="étoile"' in output)


    def test_if(self):
        handler = Document(string=
            '<img xmlns:stl="http://xml.itools.org/namespaces/stl"'
            '  stl:if="img" />')

        namespace = {'img': False}
        output = stl(handler, namespace)
        self.assertEqual(output, '')
        

    def test_if_not(self):
        handler = Document(string=
            '<img xmlns:stl="http://xml.itools.org/namespaces/stl"'
            '  stl:if="not img" />')

        namespace = {'img': True}
        output = stl(handler, namespace)
        self.assertEqual(output, '')


    def test_repeat(self):
        handler = Document(string=
            '<option xmlns:stl="http://xml.itools.org/namespaces/stl"'
            '  stl:repeat="option options" />')

        namespace = {'options': []}
        output = stl(handler, namespace)
        self.assertEqual(output, '')



if __name__ == '__main__':
    unittest.main()
