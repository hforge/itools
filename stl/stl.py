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
from itools.datatypes import Boolean, DataType, XMLAttribute
from itools import schemas
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

# Tokens
TID, TSLASH, TEOF, TREPEAT, TNONE = range(5)
token_name = ['id', 'slash', 'end of expression', 'reserved word "repeat"',
              'reserved word "none"']


keywords = {'repeat': TREPEAT, 'none': TNONE}


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
        self.expression = expression

        # Initialize semantic structures
        self.path = ()
        self.repeat = False

        # Parsing
        self.index = 0
        self.parse()
        del self.index


    ###################################################################
    # Lexical analysis
    ###################################################################
    def get_token(self):
        token = TEOF
        lexeme = None
        state = 0

        while self.index < len(self.expression):
            c = self.expression[self.index]
            if state == 0:
                self.index += 1
                if c.isalnum() or c in ('_', '.', ':'):
                    lexeme = c
                    state = 1
                elif c == '/':
                    return TSLASH, c
                else:
                    raise STLSyntaxError, 'unexpected character (%s)' % c
            elif state == 1:
                if c.isalnum() or c in ('_', '.', ':'):
                    lexeme += c
                    self.index += 1
                else:
                    break

        if lexeme is not None:
            token = keywords.get(lexeme, TID)

        return token, lexeme


    ###################################################################
    # Syntax and semantic analysis. Grammar:
    #
    #   parse = TID parser1
    #           | TREPEAT TSLASH TID TSLASH TID
    #           | TNONE
    #   parser1 = TEOF
    #             | TSLASH TID parse1
    ###################################################################
    def parse(self):
        token, lexeme = self.get_token()
        if token == TID:
            self.path = self.path + (lexeme,)
            self.parser1()
            return
        elif token == TREPEAT:
            self.repeat = True
            token, lexeme = self.get_token()
            if token == TSLASH:
                token, lexeme = self.get_token()
                if token == TID:
                    self.path = self.path + (lexeme,)
                    token, lexeme = self.get_token()
                    if token == TSLASH:
                        token, lexeme = self.get_token()
                        if token == TID:
                            self.path = self.path + (lexeme,)
                            return
        elif token == TNONE:
            return

        raise STLSyntaxError, 'unexpected %s' % token_name[token]


    def parser1(self):
        token, lexeme = self.get_token()
        if token == TEOF:
            return
        elif token == TSLASH:
            token, lexeme = self.get_token()
            if token == TID:
                self.path = self.path + (lexeme,)
                self.parser1()
                return

        raise STLSyntaxError, 'unexpected %s' % token_name[token]


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



class ContentAttr(DataType):

    @staticmethod
    def decode(data):
        return Expression(data)


    @staticmethod
    def encode(value):
        return str(value)



class AttributesAttr(DataType):

    @staticmethod
    def decode(data):
        attributes = []
        for x in data.split(';'):
            x = x.strip().split(' ', 1)
            if len(x) == 1:
                raise STLSyntaxError, \
                      'attributes expression expects two fields'

            name, expr = x
            if expr.startswith('not') and expr[3].isspace():
                expr = NotExpression(expr)
            else:
                expr = Expression(expr)
            attributes.append((name, expr))

        return tuple(attributes)


    @staticmethod
    def encode(value):
        return ';'.join([ '%s %s' % x for x in value ])



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
subs_expr = re.compile("\$\{(.+?)\}")


def substitute(data, stack, repeat_stack, encoding='utf-8'):
    data = str(data)
    def f(x):
        expr = Expression(x.group(1))
        value = expr.evaluate(stack, repeat_stack)
        return str(value)
    return subs_expr.sub(f, data)


def encode_attribute(namespace, local_name, value, encoding='UTF-8'):
    datatype = schemas.get_datatype_by_uri(namespace, local_name)
    if issubclass(datatype, Boolean):
        # XXX This representation of boolean attributes is specfic to HTML
        if value == 'False':
            return None
        if bool(value) is True:
            return local_name
    elif value is not None:
        # XXX This type-checking maybe should be replaced by something more
        # deterministic, like "datatype.encode(value)"
        if isinstance(value, unicode):
            value = value.encode(encoding)
        else:
            value = str(value)

        return XMLAttribute.encode(value)

    return None


def stl(document, namespace={}):
    # Initialize the namespace stack
    stack = NamespaceStack()
    stack.append(namespace)
    # Initialize the repeat stack (keeps repeat/index, repeat/odd, etc...)
    repeat = NamespaceStack()
    # Get the document
    s = process(document.get_root_element(), stack, repeat)
    return ''.join(s)


def process(node, stack, repeat_stack, encoding='UTF-8'):
    # Raw nodes
    if isinstance(node, unicode):
        data = node.encode(encoding)
        # Process "${...}" expressions
        data = substitute(data, stack, repeat_stack, encoding)
        return [data]
    elif isinstance(node, XML.Comment):
        return [node.to_str()]

    s = []
    # Process stl:repeat
    if node.has_attribute(stl_uri, 'repeat'):
        name, expression = node.get_attribute(stl_uri, 'repeat')

        i = 0
        values = expression.evaluate(stack, repeat_stack)
        nvalues = len(values)
        for value in values:
            # Create the new stack
            newstack = stack[:]
            newstack.append({name: value})

            newrepeat = repeat_stack[:]
            value = {'index': i,
                     'start': i == 0,
                     'end': i == nvalues - 1}
            newrepeat.append({name: value})

            # Process and append the clone
            s.extend(process1(node, newstack, newrepeat))

            # Increment counter
            i = i + 1

        return s

    s.extend(process1(node, stack, repeat_stack))
    return s


def process1(node, stack, repeat, encoding='UTF-8'):
    """
    Process stl:if, stl:attributes and stl:content.
    """
    # Remove the element if the given expression evaluates to false
    if node.has_attribute(stl_uri, 'if'):
        stl_expression = node.get_attribute(stl_uri, 'if')
        if not stl_expression.evaluate(stack, repeat):
            return []

    # Print tag name
    s = ['<%s' % node.qname]

    # Process attributes
    changed_attributes = {} # qname: value
    # Evaluate stl:attributes
    if node.has_attribute(stl_uri, 'attributes'):
        value = node.get_attribute(stl_uri, 'attributes')
        for name, expression in value:
            value = expression.evaluate(stack, repeat)
            changed_attributes[name] = value

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
        # Get the attribute value
        if qname in changed_attributes:
            value = changed_attributes.pop(qname)
        else:
            # Process "${...}" expressions
            value = substitute(value, stack, repeat, encoding)
        # Output only values different than None
        value = encode_attribute(namespace, local_name, value, encoding)
        if value is not None:
            s.append(' %s="%s"' % (qname, value))

    # Output remaining attributes
    for local_name, value in changed_attributes.items():
        value = encode_attribute(node.namespace, local_name, value, encoding)
        if value is not None:
            s.append(' %s="%s"' % (local_name, value))

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
    if node.has_attribute(stl_uri, 'content'):
        stl_expression = node.get_attribute(stl_uri, 'content')
        content = stl_expression.evaluate(stack, repeat)
        # Coerce
        if content is None:
            content = []
        elif isinstance(content, unicode):
            content = [content.encode(encoding)]
        elif isinstance(content, (int, long, float, Decimal)):
            content = [str(content)]
        elif isinstance(content, str):
            content = [content]
        else:
            msg = 'expression "%(expr)s" evaluates to value of unexpected' \
                  ' type %(type)s'
            msg = msg % {'expr': str(stl_expression),
                         'type': content.__class__.__name__}
            raise STLTypeError, msg
    else:
        content = []
        for child in node.children:
            content.extend(process(child, stack, repeat))

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


class Schema(schemas.base.Schema):

    class_uri = 'http://xml.itools.org/namespaces/stl'
    class_prefix = 'stl'


    datatypes = {'repeat': RepeatAttr,
                 'attributes': AttributesAttr,
                 'content': ContentAttr,
                 'if': IfAttr}

schemas.register_schema(Schema)
