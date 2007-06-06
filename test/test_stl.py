# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.handlers import get_handler
from itools.stl import stl
from itools.stl.stl import Expression, NamespaceStack, substitute
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

    def test_tokens(self):
        expression = Expression('a/b/c')
        self.assertEqual(expression.path, ('a', 'b', 'c'))


    def test_none(self):
        expression = Expression('none')
        self.assertEqual(expression.path, ())
        self.assertEqual(expression.evaluate(None, None), None)


    def test_traversal(self):
        namespace = {'a': {'b': {'c': 'hello world'}}}
        stack = NamespaceStack()
        stack.append(namespace)
        repeat = NamespaceStack()
        expression = Expression('a/b/c')
        value = expression.evaluate(stack, repeat)

        self.assertEqual(value, 'hello world')


    def test_attribute(self):
        handler = Document(string=
            '<img xmlns="http://www.w3.org/1999/xhtml" border="${border}" />')

        namespace = {'border': 5}
        output = stl(handler, namespace)
        expected = '<img xmlns="http://www.w3.org/1999/xhtml" border="5" />'
        self.assertEqual(output, expected)



if __name__ == '__main__':
    unittest.main()
