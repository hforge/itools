# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002-2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


import unittest
from STL import Expression, NamespaceStack, Template, \
     TID, TSLASH, TOPEN, TCLOSE, TEOF


class STLTestCase(unittest.TestCase):
    def test_tokens(self):
        expression = Expression('a/b/c')

        expected_tokens = [(TID, 'a'), (TSLASH, None), (TID, 'b'),
                           (TSLASH, None), (TID, 'c')]

        assert expression.path == ('a', 'b', 'c')
        assert expression.parameters == ()


    def test_traversal(self):
        namespace = {'a': {'b': {'c': 'hello world'}}}
        stack = NamespaceStack()
        stack.append(namespace)
        repeat = NamespaceStack()
        expression = Expression('a/b/c')
        value = expression.evaluate(stack, repeat)

        assert value == 'hello world'


    def test_function(self):
        namespace = {'translate': lambda x: x.upper()}

        class Node:
            def toxml(self):
                return 'hello world'

        stack = NamespaceStack()
        stack.append(namespace)
        repeat = NamespaceStack()
        expression = Expression('translate(content)', Node())
        value = expression.evaluate(stack, repeat)

        assert value == 'HELLO WORLD'


    def test_template(self):
        namespace = {'title': 'hello world',
                     'objects': [{'id': 'itools', 'title': 'Itaapy Tools'},
                                 {'id': 'ikaaro', 'title': 'The ikaaro CMS'}]}

        template = Template(open('test-in.html'))
        output = template(namespace)

        assert output == open('test-out.html').read()


    def test_template2(self):
        namespace = {'title': 'hello world'}
        template = Template(open('test21-in.html'))(namespace)

        namespace = {'body': template}
        template = Template(open('test20-in.html'))
        output = template(namespace)

        assert output == open('test2-out.html').read()


##    def test_nested(self):
##        """Tests a nested repeat."""
##        namespace = {'labels': [{'name': 'sex', 'values': ['woman', 'man']},
##                                {'name': 'age', 'values': ['-18', '+18']}]}

##        stl = '<stl:block repeat="label labels">' \
##              '  <stl:block content="label/name" />:' \
##              '  <stl:block repeat="value label/values"' \
##              '             content="value" />' \
##              '</stl:block>'
##        template = Template(stl)

##        print template(namespace)



if __name__ == '__main__':
    unittest.main()
