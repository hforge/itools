# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

"""
STL stands for Simple Template Language, as it is the simplest template
language I could imagine.
"""

# Import from the Standard Library
from decimal import Decimal
import re

# Import from itools
from itools.datatypes import (Boolean, DataType, URI, XMLAttribute,
    XML as XMLContent)
from itools.schemas import (Schema as BaseSchema, get_datatype_by_uri,
                            register_schema)
from itools.xml import XML, namespaces



stl_uri = 'http://xml.itools.org/namespaces/stl'


########################################################################
# Exceptions
########################################################################
class STLSyntaxError(XML.XMLError):
    pass


class STLNameError(NameError):
    pass


class STLTypeError(TypeError):
    pass


########################################################################
# Expressions
########################################################################

class Expression(object):
    """
    Parses and evaluates stl expressions.
    
    Examples of allowed expressions:
    
      none
      a
      a/b/c
      repeat/a/index
      ...
    """

    def __init__(self, expression):
        self.repeat = False
        # none
        if expression == 'none':
            self.path = ()
        else:
            path = expression.split('/')
            for x in path:
                if x == '':
                    raise STLSyntaxError, 'malformed STL expression'
            # repeat
            if path[0] == 'repeat':
                self.repeat = True
                path = path[1:]
                if len(path) != 2:
                    raise STLSyntaxError, 'malformed STL expression'
            self.path = tuple(path)


    ###################################################################
    # API
    ###################################################################
    def evaluate(self, stack, repeat):
        if not self.path:
            return None

        if self.repeat:
            stack = repeat

        # Traverse
        x = stack.lookup(self.path[0])
        for name in self.path[1:]:
            x = lookup(x, name)

        # Call
        if callable(x):
            try:
                x = x()
            except AttributeError, error_value:
                # XXX "callable" could return true even if the object is not
                # callable (see Python's documentation).
                #
                # This happens, for example, in the context of Zope, maybe
                # because of extension classes and acquisition. So we catch
                # the AttributeError exception, we should test also for the
                # exception value to be "__call__". This is dangereous
                # because we could hide real errors. Further exploration
                # needed..
                pass

        return x


    def __str__(self):
        if not self.path:
            return 'none'
        s = '/'.join(self.path)
        if self.repeat is True:
            return 'repeat/%s' % s
        return s


############################################################################
# Boolean expressions
class NotExpression(Expression):

    def __init__(self, expression):
        expression = expression[3:].strip()
        Expression.__init__(self, expression)


    def evaluate(self, stack, repeat):
        value = Expression.evaluate(self, stack, repeat)
        return not value


    def __str__(self):
        return 'not %s' % Expression.__str__(self)


###########################################################################
# Namespace
###########################################################################
def lookup(namespace, name):
    """
    Looks for a variable in a namespace (an instance, a mapping, etc..)
    """
    if hasattr(namespace, 'stl_lookup'):
        return namespace.stl_lookup(name)
    elif isinstance(namespace, dict):
        if name in namespace:
            return namespace[name]
    elif hasattr(namespace, name):
        return getattr(namespace, name)

    raise STLNameError, 'name "%s" not found in the namespace' % name



class NamespaceStack(list):
    """
    This class represents a namespace stack as used by STL. A variable
    is looked up in the stack from the top to the bottom until found.
    """

    def lookup(self, name):
        stack = self[:]
        stack.reverse()
        for namespace in stack:
            try:
                return lookup(namespace, name)
            except STLNameError:
                pass

        raise STLNameError, 'name "%s" not found in the namespace' % name


    def __getslice__(self, a, b):
        return self.__class__(list.__getslice__(self, a, b))





###########################################################################
# The tree
###########################################################################

class Element(XML.Element):

    namespace = stl_uri

    def is_block(self):
        return self.name == 'block'


    def is_inline(self):
        return self.name == 'inline'



class IfAttr(DataType):

    @staticmethod
    def decode(data):
        if data.startswith('not') and data[3].isspace():
            return NotExpression(data)
        return Expression(data)


    @staticmethod
    def encode(value):
        return str(value)



class RepeatAttr(DataType):

    @staticmethod
    def decode(data):
        name, expression = data.split(' ', 1)
        return name, Expression(expression)


    @staticmethod
    def encode(value):
        return '%s %s' % value



########################################################################
# The run-time engine
########################################################################
subs_expr_solo = re.compile("^\$\{([\w\/:]+?)\}$")
subs_expr = re.compile("\$\{(.+?)\}")


def substitute_boolean(data, stack, repeat_stack, encoding='utf-8'):
    if isinstance(data, bool):
        return data

    match = subs_expr_solo.match(data)
    if match is None:
        return True
    expr = Expression(match.group(1))
    value = expr.evaluate(stack, repeat_stack)
    return bool(value)


def substitute(data, stack, repeat_stack, encoding='utf-8'):
    if isinstance(data, str):
        pass
    elif isinstance(data, unicode):
        data = data.encode('utf-8')
    else:
        data = str(data)
    # Solo, preserve the value None
    match = subs_expr_solo.match(data)
    if match is not None:
        expr = Expression(match.group(1))
        value = expr.evaluate(stack, repeat_stack)
        # Preserve the value None
        if value is None:
            return None, 1
        # Send the string
        if isinstance(value, unicode):
            return value.encode(encoding), 1
        return str(value), 1
    # A little more complex
    def repl(match):
        expr = Expression(match.group(1))
        value = expr.evaluate(stack, repeat_stack)
        # Remove if None
        if value is None:
            return ''
        # Send the string
        if isinstance(value, unicode):
            return value.encode(encoding)
        return str(value)
    return subs_expr.subn(repl, data)


def stl(document, namespace={}, prefix=None):
    # Initialize the namespace stack
    stack = NamespaceStack()
    stack.append(namespace)
    # Initialize the repeat stack (keeps repeat/index, repeat/odd, etc...)
    repeat = NamespaceStack()
    # Get the document
    s = process(document.get_root_element(), stack, repeat, prefix=prefix)
    return ''.join(s)


def process(node, stack, repeat_stack, encoding='UTF-8', prefix=None):
    # Raw nodes
    if isinstance(node, unicode):
        data = node.encode(encoding)
        data = XMLContent.encode(data)
        # Process "${...}" expressions
        data, kk = substitute(data, stack, repeat_stack, encoding)
        if data is None:
            return []
        return [data]
    elif isinstance(node, XML.Comment):
        return [node.to_str()]

    s = []
    # Process stl:repeat
    if node.has_attribute(stl_uri, 'repeat'):
        name, expression = node.get_attribute(stl_uri, 'repeat')

        i = 0
        values = expression.evaluate(stack, repeat_stack)
        try:
            nvalues = len(values)
        except TypeError:
            raise STLTypeError, 'stl:repeat expects a countable value, "%s" is not' % expression
        for value in values:
            # Create the new stack
            newstack = stack[:]
            newstack.append({name: value})

            newrepeat = repeat_stack[:]
            value = {'index': i,
                     'start': i == 0,
                     'end': i == nvalues - 1,
                     'even': 'odd' if i % 2 else 'even'}
            newrepeat.append({name: value})

            # Process and append the clone
            s.extend(process1(node, newstack, newrepeat, prefix=prefix))

            # Increment counter
            i = i + 1

        return s

    s.extend(process1(node, stack, repeat_stack, prefix=prefix))
    return s


def resolve_pointer(uri, offset):
    uri = URI.decode(uri)
    if not uri.scheme and not uri.authority:
        if uri.path.is_relative():
            if uri.path or str(uri) == '.':
                # XXX Here we loss the query and fragment.
                value = offset.resolve(uri.path)
                return str(value)

    return URI.encode(uri)


def process1(node, stack, repeat, encoding='UTF-8', prefix=None):
    """
    Process "stl:if" and variable substitution.
    """
    # Remove the element if the given expression evaluates to false
    if node.has_attribute(stl_uri, 'if'):
        stl_expression = node.get_attribute(stl_uri, 'if')
        if not stl_expression.evaluate(stack, repeat):
            return []

    # Print tag name
    s = ['<%s' % node.qname]

    # Process attributes
    xmlns_uri = namespaces.XMLNSNamespace.class_uri

    # Output existing attributes
    for namespace, local_name, value in node.get_attributes():
        # Omit stl attributes
        if namespace == stl_uri:
            continue
        # Omit stl namespace
        if namespace == xmlns_uri and local_name == 'stl':
            continue

        qname = node.get_attribute_qname(namespace, local_name)
        # Process "${...}" expressions
        datatype = get_datatype_by_uri(namespace, local_name)
        # Boolean attributes
        if issubclass(datatype, Boolean):
            value = substitute_boolean(value, stack, repeat, encoding)
            if value is True:
                s.append(' %s="%s"' % (qname, local_name))
            continue
        # Non Boolean attributes
        value, n = substitute(value, stack, repeat, encoding)
        # Output only values different than None
        if value is None:
            continue
        # Rewrite URLs (XXX specific to HTML)
        xhtml_ns = 'http://www.w3.org/1999/xhtml'
        if prefix is None or n > 0:
            value = XMLAttribute.encode(value)
            s.append(' %s="%s"' % (qname, value))
            continue
        if node.namespace == xhtml_ns and namespace == xhtml_ns:
            # <... src="X" />
            if local_name == 'src':
                value = resolve_pointer(value, prefix)
            # <link href="X" />
            elif node.name == 'link':
                if local_name == 'href':
                    value = resolve_pointer(value, prefix)
            # <param name="movie" value="X" />
            elif node.name == 'param':
                if local_name == 'value':
                    param_name = node.get_attribute(namespace, 'name')
                    if param_name == 'movie':
                        value = resolve_pointer(value, prefix)
        value = XMLAttribute.encode(value)
        s.append(' %s="%s"' % (qname, value))

    # The element schema, we need it
    namespace = namespaces.get_namespace(node.namespace)
    schema = namespace.get_element_schema(node.name)
    is_empty = schema.get('is_empty', False)
    # Close the open tag
    if is_empty:
        s.append('/>')
    else:
        s.append('>')

    # Process the content
    content = []
    for child in node.children:
        content.extend(process(child, stack, repeat, prefix=prefix))

    # Remove the element but preserves its children if it is a stl:block or
    # a stl:inline
    if isinstance(node, Element):
        return content

    s.extend(content)
    if not is_empty:
        s.append('</%s>' % node.qname)
    return s


########################################################################
# The XML namespace handler
########################################################################

elements_schema = {
    'block': {'type': Element},
    'inline': {'type': Element}
    }


class Namespace(namespaces.AbstractNamespace):

    class_uri = 'http://xml.itools.org/namespaces/stl'
    class_prefix = 'stl'


    @staticmethod
    def get_element_schema(name):
        try:
            return elements_schema[name]
        except KeyError:
            raise STLSyntaxError, 'unexpected element name: %s' % name

namespaces.set_namespace(Namespace)


class Schema(BaseSchema):

    class_uri = 'http://xml.itools.org/namespaces/stl'
    class_prefix = 'stl'


    datatypes = {'repeat': RepeatAttr,
                 'if': IfAttr}

register_schema(Schema)
