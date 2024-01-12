# Copyright (C) 2004-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from unittest import TestCase, main

# Import from itools
import itools.html
from itools.stl import stl
from itools.stl.stl import NamespaceStack, substitute, evaluate
from itools.xml import stream_to_str
from itools.xmlfile import XMLFile


class SubstituteTestCase(TestCase):

    def setUp(self):
        namespace = {'name': 'Toto'}

        self.stack = NamespaceStack()
        self.stack.append(namespace)
        self.repeat = NamespaceStack()


    def test_simple(self):
        data = 'Hello ${name}'
        stream = substitute(data, self.stack, self.repeat)
        # Assert
        out = stream_to_str(stream)
        self.assertEqual(out, 'Hello Toto')



class STLTestCase(TestCase):

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
        handler = XMLFile(string=
            '<img xmlns="http://www.w3.org/1999/xhtml" alt="${alt}" />')
        namespace = {'alt': 'My title'}
        stream = stl(handler, namespace)
        # Assert
        events = list(stream)
        value = events[0][1][2][(None, 'alt')]
        self.assertEqual(value, 'My title')


    def test_attribute_accent(self):
        handler = XMLFile(string=
            '<input xmlns="http://www.w3.org/1999/xhtml" value="${name}" />')
        namespace = {'name': 'étoile'}
        stream = stl(handler, namespace)
        # Assert
        events = list(stream)
        value = events[0][1][2][(None, 'value')]
        self.assertEqual(value, 'étoile')


    def test_if(self):
        handler = XMLFile(string=
            '<img xmlns:stl="http://www.hforge.org/xml-namespaces/stl"'
            '  stl:if="img" />')
        namespace = {'img': False}
        stream = stl(handler, namespace)
        # Assert
        events = list(stream)
        self.assertEqual(events, [])


    def test_if_not(self):
        handler = XMLFile(string=
            '<img xmlns:stl="http://www.hforge.org/xml-namespaces/stl"'
            '  stl:if="not img" />')
        namespace = {'img': True}
        stream = stl(handler, namespace)
        # Assert
        events = list(stream)
        self.assertEqual(events, [])


    def test_repeat(self):
        handler = XMLFile(string=
            '<option xmlns:stl="http://www.hforge.org/xml-namespaces/stl"'
            '  stl:repeat="option options" />')
        namespace = {'options': []}
        stream = stl(handler, namespace)
        # Assert
        events = list(stream)
        self.assertEqual(events, [])



if __name__ == '__main__':
    main()
