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

# Import from Python
import unittest

# Import from itools
from itools.resources import get_resource
from itools.handlers import get_handler
from STL import Expression, NamespaceStack, TID, TSLASH, TOPEN, TCLOSE, TEOF, TNONE


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
        output = template.stl(namespace)

        assert output == get_handler('test-out.xml').to_unicode()


    def test_template2(self):
        namespace = {'title': 'hello world'}
        template = get_handler('test21-in.xml')
        template = template.stl(namespace)

        namespace = {'body': template}
        template = get_handler('test20-in.xml')
        output = template.stl(namespace)

        assert output == get_handler('test2-out.xml').to_unicode()


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

##        print template.stl(namespace)



if __name__ == '__main__':
    unittest.main()
