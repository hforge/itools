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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from the Standard Library
import unittest

# Import from itools
from itools.resources import get_resource
from itools.handlers import get_handler
from stl import Expression, NamespaceStack
from stl import TID, TSLASH, TOPEN, TCLOSE, TEOF, TNONE
from stl import stl


class STLTestCase(unittest.TestCase):
    def test_tokens(self):
        expression = Expression('a/b/c')

        expected_tokens = [(TID, 'a'), (TSLASH, None), (TID, 'b'),
                           (TSLASH, None), (TID, 'c')]

        assert expression.path == ('a', 'b', 'c')
        assert expression.parameters == ()


    def test_none(self):
        expression = Expression('none')
        expected_tokens = [(TNONE, 'none')]

        assert expression.path == ()
        assert expression.parameters == ()
        assert expression.evaluate(None, None) == None


    def test_traversal(self):
        namespace = {'a': {'b': {'c': 'hello world'}}}
        stack = NamespaceStack()
        stack.append(namespace)
        repeat = NamespaceStack()
        expression = Expression('a/b/c')
        value = expression.evaluate(stack, repeat)

        assert value == 'hello world'


    def test_function(self):
        namespace = {'sum': lambda x: str(sum(range(1, int(x) + 1)))}

        class Node:
            def toxml(self):
                return 'hello world'

        stack = NamespaceStack()
        stack.append(namespace)
        repeat = NamespaceStack()
        expression = Expression('sum(5)')
        value = expression.evaluate(stack, repeat)

        assert value == '15'


    def test_template(self):
        namespace = {'title': 'hello world',
                     'objects': [{'id': 'itools', 'title': 'Itaapy Tools'},
                                 {'id': 'ikaaro', 'title': 'The ikaaro CMS'}]}

        template = get_handler('test-in.xml')
        output = stl(template, namespace)

        assert output == get_handler('test-out.xml').to_str()


    def test_template2(self):
        namespace = {'title': 'hello world'}
        template = get_handler('test21-in.xml')
        template = stl(template, namespace)

        namespace = {'body': template}
        template = get_handler('test20-in.xml')
        output = stl(template, namespace)

        assert output == get_handler('test2-out.xml').to_str()


##    def test_nested(self):
##        """Tests a nested repeat."""
##        namespace = {'labels': [{'name': 'sex', 'values': ['woman', 'man']},
##                                {'name': 'age', 'values': ['-18', '+18']}]}

##        stl = '<stl:block repeat="label labels">' \
##              '  <stl:block content="label/name" />:' \
##              '  <stl:block repeat="value label/values"' \
##              '             content="value" />' \
##              '</stl:block>'
##        resource = memory.File(stl)
##        template = XML.Document(resource)

##        print stl(template, namespace)



if __name__ == '__main__':
    unittest.main()
